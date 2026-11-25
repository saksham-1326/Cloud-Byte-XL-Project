// Pure boundary helpers, shared by the React UI and independent Node contracts.
export function validateRepositoryResponse(value) {
  if (!value || value.status !== 'SUCCESS' || !value.repository?.url || !value.repository?.name) throw new Error('Repository response is incomplete.');
  for (const key of ['files','languages','contributors','commits']) if (value[key] !== undefined && !Array.isArray(value[key])) throw new Error(`Repository ${key} response is invalid.`);
  if (value.analysis) for (const key of ['issues','recommendations','subscores']) if (value.analysis[key] !== undefined && !Array.isArray(value.analysis[key])) throw new Error(`Analysis ${key} response is invalid.`);
  return value;
}
export function validateIntelligenceResponse(value, repository) {
  // GitHub names are case-insensitive; the Flask allowlist normalizes to lowercase.
  if (typeof value?.repository !== 'string' || typeof repository !== 'string' || value.repository.toLowerCase() !== repository.toLowerCase()) throw new Error('Intelligence response belongs to a different repository.');
  for (const key of ['runs','reports','predictions','model_versions']) if (!Array.isArray(value[key])) throw new Error(`Intelligence ${key} response is invalid.`);
  if (value.runs.some(run => !Number.isSafeInteger(run.run_id) || !Number.isInteger(run.attempt) || run.attempt < 1)) throw new Error('Workflow attempt identity is invalid.');
  return value;
}
export function filePaths(files = []) {
  return [...new Set(files.map(f => typeof f === 'string' ? f : f?.path).filter(p => typeof p === 'string' && p))].sort();
}
export function configurationPaths(paths, kind) {
  return paths.filter(path => kind === 'Docker'
    ? /(^|\/)(Dockerfile[^/]*|[^/]*\.dockerfile|docker-compose[^/]*|compose\.ya?ml|\.dockerignore)$/i.test(path)
    : /(^|\/)(k8s|kubernetes|helm|charts)\/|(^|\/)(deployment|service|ingress|statefulset|daemonset|configmap|secret|chart|values)\.ya?ml$/i.test(path));
}
export function sourceLink(repo, path, line) {
  if (!repo?.url?.startsWith('https://github.com/')) return undefined;
  return `${repo.url.replace(/\/+$/, '')}/blob/${encodeURIComponent(repo.analysisCommitSha || repo.branch)}/${path.split('/').map(encodeURIComponent).join('/')}${line ? `#L${line}` : ''}`;
}
export function matchingReports(reports, run) {
  return run ? reports.filter(r => r.run_id === run.run_id && r.attempt === run.attempt) : [];
}
export function evidenceAnchor(reportId, evidenceId, index) {
  return `evidence-${encodeURIComponent(reportId)}-${encodeURIComponent(evidenceId)}-${index}`;
}
export function navigationMatches(destinations, query) {
  return destinations.filter(item => `${item.label} ${item.hint}`.toLowerCase().includes(query.trim().toLowerCase()));
}
export function exportRepository(snapshot) {
  if (!snapshot?.analysis) throw new Error('Complete a repository analysis before exporting.');
  // Explicit allowlist: never serialize component state, admin headers or tokens.
  return { repository:snapshot.repository, health:{overall:snapshot.analysis.overall ?? null,status:snapshot.analysis.status},
    subscores:snapshot.analysis.subscores || [],security:snapshot.analysis.security || null,issues:snapshot.analysis.issues || [],
    recommendations:snapshot.analysis.recommendations || [],architecture:snapshot.analysis.architecture || null,
    provenance:{analysisCommitSha:snapshot.repository.analysisCommitSha || null,source:'repository_analysis',runtimeTelemetry:false} };
}
