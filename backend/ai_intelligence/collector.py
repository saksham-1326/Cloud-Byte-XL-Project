"""Incremental ingestion keyed by repository/run/attempt; historical SHA snapshots."""
import re
from .github import GitHubError, scrub, repository_name


def validate_attempt(repo, run_id, attempt, run, jobs):
    """Validate exact live metadata before scoped observer persistence."""
    repo=repository_name(repo)
    if (type(run.get('id')) is not int or type(run.get('run_attempt')) is not int
        or run.get('id')!=run_id or run.get('run_attempt')!=attempt
        or not isinstance(run.get('head_sha'),str) or not re.fullmatch(r'[a-fA-F0-9]{40}',run['head_sha'])
        or type(run.get('workflow_id')) is not int or run['workflow_id']<1
        or repository_name(run.get('repository',{}).get('full_name'))!=repo):
        raise ValueError('Run identity does not match the configured repository and attempt.')
    for job in jobs:
        if (type(job.get('run_id')) is not int or job.get('run_id')!=run_id or job.get('run_attempt',attempt)!=attempt
            or (job.get('head_sha') and job['head_sha']!=run['head_sha'])):
            raise ValueError('Job identity does not match the exact run attempt.')


def synchronize_attempt(client, store, repo, run_id, attempt):
    """Scoped outcome reconciliation, reusing existing transactional save_run.

    Metadata only: no failure logs, training, provider calls or historical
    backfills. Existing full-history synchronize behavior remains unchanged.
    """
    run=client.run(repo,run_id,attempt)
    jobs=client.jobs(repo,run_id,attempt)
    validate_attempt(repo,run_id,attempt,run,jobs)
    if run.get('status')!='completed' or not run.get('conclusion'):
        return {'reconciled':False,'run':run,'jobs':jobs}
    store.save_run(repo,scrub(run),scrub(jobs))
    return {'reconciled':True,'run':run,'jobs':jobs}


def synchronize(client, store, repo):
    repo=repository_name(repo)
    metadata=client.get(f"/repos/{repo}")
    count=0
    warnings=[]
    for latest in client.runs(repo):
        for attempt in range(1,int(latest.get("run_attempt",1))+1):
            previous=store.run(repo,latest["id"],attempt)
            if previous and previous["status"]=="completed":
                path=previous["payload"].get("path","").split("@")[0]
                old_jobs=store.jobs(repo,latest["id"],attempt)
                if store.snapshot(repo,previous["commit_sha"],path) and old_jobs and all(
                    j["payload"].get("status")=="completed" and
                    (j["payload"].get("conclusion")!="failure" or j["log_status"] in ("available","unavailable_expired"))
                    for j in old_jobs
                ):
                    continue
            run=latest if attempt==latest.get("run_attempt",1) else client.run(repo,latest["id"],attempt)
            run=scrub(run)
            run["repository_id"]=metadata["id"]
            jobs=scrub(client.jobs(repo,run["id"],attempt))
            for job in jobs:
                job["log_status"]="pending" if job.get("status")!="completed" else "not_requested_success"
                if job.get("conclusion")=="failure":
                    try:
                        job["log_text"]=client.job_log(repo,job["id"])
                        job["log_status"]="available"
                    except GitHubError as error:
                        if error.status==429: raise
                        job["log_status"]="unavailable_expired" if error.status in (404,410) else "deferred"
                        warnings.append({"run_id":run["id"],"job_id":job["id"],"message":str(error)})
            store.save_run(repo,run,jobs)
            if run.get("status")=="completed" and not jobs:
                warnings.append({"run_id":run["id"],"message":"No jobs returned for completed attempt; collection will retry on the next sync."})
            path=run.get("path","").split("@")[0]
            if not store.snapshot(repo,run["head_sha"],path):
                try:
                    store.save_snapshot(repo,client.snapshot(repo,run))
                except GitHubError as error:
                    if error.status==429: raise
                    warnings.append({"run_id":run["id"],"message":"Historical snapshot incomplete: "+str(error)})
            count+=1
    return {"repository":repo,"processed_attempts":count,"stored_attempts":len(store.runs(repo)),"warnings":warnings}
