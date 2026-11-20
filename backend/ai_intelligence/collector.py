"""Incremental ingestion keyed by repository/run/attempt; historical SHA snapshots."""
from .github import GitHubError, scrub, repository_name


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
