"""Pre-outcome features, purged chronological evaluation, experimental sklearn baselines."""
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, average_precision_score, roc_auc_score, brier_score_loss
from .store import timestamp, label

FEATURE_VERSION="prequeue-v2-utc-standardized"
ARTIFACTS=Path(__file__).resolve().parents[1]/"ai_artifacts"


def features(target, history, snapshot, at):
    if snapshot.get("historical_ref")!=target["commit_sha"] or snapshot.get("sha")!=target["commit_sha"]:
        raise ValueError("Historical configuration must match the target commit SHA.")
    at=timestamp(at).astimezone(timezone.utc)
    prior={}
    for run in history:
        if (run["workflow_id"]!=target["workflow_id"] or run["run_id"]==target["run_id"] or run["commit_sha"]==target["commit_sha"] or not run.get("completed_at") or timestamp(run["completed_at"])>=at or label(run.get("conclusion")) is None):
            continue
        if run["run_id"] not in prior or run["attempt"]>prior[run["run_id"]]["attempt"]:
            prior[run["run_id"]]=run
    ordered=sorted(prior.values(),key=lambda r:timestamp(r["completed_at"]));recent=ordered[-10:]
    streak=0
    for run in reversed(ordered):
        if label(run["conclusion"])!=1:break
        streak+=1
    files=snapshot["files"];paths=[item["filename"].lower() for item in files]
    durations=[r["payload"].get("duration_seconds") for r in recent if r["payload"].get("duration_seconds") is not None]
    values={"changed_files":len(files),"additions":sum(f.get("additions",0) for f in files),"deletions":sum(f.get("deletions",0) for f in files),
            "dependency_change":int(any(p.endswith(("requirements.txt","package-lock.json","yarn.lock","pyproject.toml","poetry.lock")) for p in paths)),
            "docker_change":int(any("dockerfile" in p or "docker-compose" in p for p in paths)),
            "workflow_change":int(any(p.startswith(".github/workflows/") for p in paths)),
            "workflow_config_available":int(snapshot.get("config_status")=="available"),
            "workflow_lines":len((snapshot.get("workflow_config") or "").splitlines()),
            "prior_run_count":len(ordered),"recent_failure_rate":mean(label(r["conclusion"]) for r in recent) if recent else 0.0,
            "consecutive_failures":streak,"prior_mean_duration":mean(durations) if durations else 0.0,
            "prior_duration_count":len(durations),"event":target["payload"].get("event") or "unknown",
            "workflow_identity":str(target["workflow_id"]),"created_hour":at.hour,"created_weekday":at.weekday()}
    provenance={"feature_version":FEATURE_VERSION,"prediction_time":at.isoformat(),"historical_ref":snapshot["sha"],
                "prior_runs":[{"run_id":r["run_id"],"attempt":r["attempt"],"completed_at":timestamp(r["completed_at"]).isoformat()} for r in ordered],
                "excluded":"Target outcome/duration/logs/jobs/security findings; same-commit siblings; outcomes not complete before prediction time.",
                "limitation":"Changed files use the head commit diff, not an inferred full pull-request merge diff."}
    return values,provenance


def metrics(y, probabilities, threshold):
    y=np.asarray(y);p=np.asarray(probabilities);pred=(p>=threshold).astype(int)
    both=len(set(y.tolist()))==2
    bins=[]
    for low,high in [(0,.33),(.33,.66),(.66,1.00001)]:
        mask=(p>=low)&(p<high)
        if mask.any():bins.append({"count":int(mask.sum()),"mean_probability":float(p[mask].mean()),"observed_failure_rate":float(y[mask].mean())})
    return {"n":len(y),"accuracy":float(accuracy_score(y,pred)),"precision":float(precision_score(y,pred,zero_division=0)),"recall":float(recall_score(y,pred,zero_division=0)),"f1":float(f1_score(y,pred,zero_division=0)),
            "confusion_matrix":confusion_matrix(y,pred,labels=[0,1]).tolist(),"pr_auc":float(average_precision_score(y,p)) if both else None,
            "roc_auc":float(roc_auc_score(y,p)) if both else None,"brier_score":float(brier_score_loss(y,p)),"calibration_bins":bins,
            "calibration_status":"descriptive_only_insufficient_sample" if len(y)<100 else "descriptive_not_recalibrated"}


def temporal_split(rows):
    rows=sorted(rows,key=lambda row:timestamp(row["run"]["created_at"]))
    a=int(len(rows)*.6);b=int(len(rows)*.8)
    train=rows[:a];seen={r["run"]["commit_sha"] for r in train}
    validation=[r for r in rows[a:b] if r["run"]["commit_sha"] not in seen]
    seen.update(r["run"]["commit_sha"] for r in validation)
    test=[r for r in rows[b:] if r["run"]["commit_sha"] not in seen]
    if test:
        validation=[r for r in validation if timestamp(r["run"]["completed_at"])<timestamp(test[0]["run"]["created_at"])]
    # At the first validation/test prediction, training outcomes must already exist.
    if validation:
        cutoff=timestamp(validation[0]["run"]["created_at"])
        train=[r for r in train if timestamp(r["run"]["completed_at"])<cutoff]
    return train,validation,test


def train(store,repo):
    runs=store.runs(repo);rows=[];excluded=[]
    for run in runs:
        if label(run.get("conclusion")) is None or run["attempt"]!=1 or not run.get("completed_at"):
            excluded.append({"run_id":run["run_id"],"reason":"unlabeled, rerun attempt, or completion timestamp unavailable"});continue
        path=run["payload"].get("path","").split("@")[0];snapshot=store.snapshot(repo,run["commit_sha"],path)
        if not snapshot:
            excluded.append({"run_id":run["run_id"],"reason":"historical snapshot unavailable"});continue
        values,provenance=features(run,runs,snapshot,run["created_at"])
        store.features(repo,run,values,provenance,run["created_at"])
        rows.append({"run":run,"values":values,"provenance":provenance,"label":label(run["conclusion"])})
    training,validation,test=temporal_split(rows)
    version=str(uuid.uuid4())
    result={"feature_version":FEATURE_VERSION,"preprocessing":"DictVectorizer + train-only StandardScaler", "version":version,"status":"insufficient_data","dataset_size":len(rows),"class_distribution":{"success":sum(r["label"]==0 for r in rows),"failure":sum(r["label"]==1 for r in rows)},
            "split_sizes":{"train":len(training),"validation":len(validation),"test":len(test)},"excluded":excluded,
            "evaluation_date":datetime.now(timezone.utc).isoformat(),"label_policy":"Only success=0 and failure=1; all other conclusions excluded. Attempts >1 excluded from training.",
            "split_policy":"Chronological 60/20/20; purge shared commits across partitions; train outcomes must precede validation predictions.",
            "limitation":"Small, repository-specific data with deliberately induced failures. Not evidence of production generalization."}
    if len(rows)<12 or len(training)<6 or len(validation)<2 or len(test)<2 or min(sum(r['label']==v for r in training) for v in [0,1])<2:
        result["reason"]="Insufficient independent chronological samples or class diversity for defensible fitting/evaluation."
        store.model(repo,version,result);return result
    X=[r["values"] for r in training];y=[r["label"] for r in training]
    candidates={"dummy":DummyClassifier(strategy="prior"),"logistic":LogisticRegression(max_iter=2000,class_weight="balanced",random_state=42),"random_forest":RandomForestClassifier(n_estimators=100,max_depth=4,min_samples_leaf=2,class_weight="balanced",random_state=42,n_jobs=1)}
    scored={};fitted={}
    for name,model in candidates.items():
        pipeline=make_pipeline(DictVectorizer(sparse=False),StandardScaler(),model);pipeline.fit(X,y)
        p=pipeline.predict_proba([r["values"] for r in validation])[:,1]
        choices=[.5] if len({r['label'] for r in validation})<2 else [.2,.3,.4,.5,.6,.7,.8]
        threshold=max(choices,key=lambda t:(metrics([r['label'] for r in validation],p,t)['f1'],-abs(.5-t)))
        scored[name]={"threshold":threshold,"validation":metrics([r['label'] for r in validation],p,threshold)};fitted[name]=pipeline
    selected=max(scored,key=lambda name:(scored[name]['validation']['f1'],-scored[name]['validation']['brier_score']))
    pipeline=fitted[selected];threshold=scored[selected]['threshold']
    probabilities=pipeline.predict_proba([r['values'] for r in test])[:,1]
    # Evaluate every comparator on the same untouched test interval, not just the winner.
    for name,p in fitted.items():
        scored[name]['test']=metrics([r['label'] for r in test],p.predict_proba([r['values'] for r in test])[:,1],scored[name]['threshold'])
    result.update(status="experimental",selected_model=selected,threshold=threshold,comparisons=scored,test=scored[selected]['test'],
                  threshold_policy="Validation F1; 0.5 when validation has only one class.",
                  trained_through=max(timestamp(r['run']['completed_at']) for r in training).isoformat(),
                  feature_names=pipeline[0].get_feature_names_out().tolist(),
                  backtest=[{"run_id":r['run']['run_id'],"attempt":r['run']['attempt'],"probability":float(p),"label":r['label'],"features":r['values'],"feature_time":r['provenance']['prediction_time']} for r,p in zip(test,probabilities)])
    ARTIFACTS.mkdir(exist_ok=True);path=ARTIFACTS/(version+".joblib")
    joblib.dump(pipeline,path);digest=hashlib.sha256(path.read_bytes()).hexdigest()
    store.model(repo,version,result,str(path),digest)
    return result


def load_model(model):
    path=Path(model['artifact_path']).resolve()
    if path.parent!=ARTIFACTS.resolve() or path.name!=str(model['version'])+'.joblib' or hashlib.sha256(path.read_bytes()).hexdigest()!=model['artifact_sha256']:
        raise ValueError("Model artifact integrity verification failed.")
    return joblib.load(path)
