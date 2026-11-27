import {Files, AlertCircle, AlertOctagon, Cloud, ShieldAlert} from "lucide-react";

/* Repository data is populated exclusively from the Flask response. */
let REPO = {name:"",fullName:"",url:"",branch:"",lastCommitMsg:"",commitHash:"",commitAuthor:"",lastAnalyzed:"Not analyzed",analysisDuration:"—"};
let HEALTH = {overall:0,status:"Analysis unavailable"};
let SUBSCORES = [];
let METRICS = [
  {label:"Total Files",value:"0",icon:Files,note:"Repository files"},
  {label:"Issues Detected",value:"0",icon:AlertCircle,note:"Latest analysis"},
  {label:"Critical Issues",value:"0",icon:AlertOctagon,note:"Latest analysis",tone:"critical"},
  {label:"Cloud Resources",value:"0",icon:Cloud,note:"Detected resources"},
  {label:"Security Findings",value:"0",icon:ShieldAlert,note:"Latest analysis"},
];
let SEVERITY_COUNTS = {critical:0,high:0,medium:0,low:0};
let ISSUES = [];
let ARCH = {title:"Repository Architecture",reason:"Evidence from the connected repository.",assessment:"No cloud resource evidence detected.",provider:"Not detected",confidence:0,services:[],architectureLabels:[],detected:{},evidence:[]};
let SECURITY = {score:0,findings:{critical:0,high:0,medium:0,low:0}};
let RECOMMENDATIONS = [];
let ACTIVITY = [];
let CONTRIBUTORS = [];
let COMMITS = [];
let LANGUAGES = [];
let REPOSITORY_FILES = [];
const ANALYSIS_STEPS = ["Repository metadata", "File discovery", "Source inspection", "Configuration analysis", "Security findings", "Report generation"];
let ANALYSIS_HISTORY = [];
let HISTORY_REPO = "";

function applyAnalysisData(analysis) {
  if (!analysis) {
    HEALTH={overall:null,status:"Analysis unavailable"};SUBSCORES=[];ISSUES=[];RECOMMENDATIONS=[];
    SEVERITY_COUNTS={critical:0,high:0,medium:0,low:0};SECURITY={score:null,findings:SEVERITY_COUNTS};
    ARCH={title:"Repository Architecture",reason:"No analysis returned.",assessment:"Analysis unavailable.",provider:"Not detected",confidence:0,services:[],architectureLabels:[],detected:{},evidence:[]};
    ACTIVITY=[];METRICS=METRICS.map(m=>m.label==="Total Files" ? m : {...m,value:"—",note:"Analysis unavailable"});
    return;
  }

  HEALTH = {
    overall: Number(analysis.overall ?? 0),
    status: analysis.status || "Analysis completed",
  };

  SUBSCORES = Array.isArray(analysis.subscores) ? analysis.subscores : [];
  ISSUES = Array.isArray(analysis.issues) ? analysis.issues : [];
  SEVERITY_COUNTS = analysis.severityCounts || { critical: 0, high: 0, medium: 0, low: 0 };
  SECURITY = analysis.security || { score: null, findings: SEVERITY_COUNTS };
  RECOMMENDATIONS = Array.isArray(analysis.recommendations) ? analysis.recommendations : [];

  const architecture = analysis.architecture || {};
  const detectedArchitecture = architecture.detected || {};
  ARCH = {
    ...ARCH,
    title: architecture.title || "Repository Architecture",
    reason: architecture.reason || "Architecture is determined from repository evidence.",
    assessment: architecture.cloudAssessment || "No cloud resource evidence was detected.",
    provider: architecture.provider || "Not detected",
    confidence: Number(architecture.confidence ?? 0),
    services: Array.isArray(detectedArchitecture.cloudResources)
      ? detectedArchitecture.cloudResources
      : [],
    architectureLabels: Array.isArray(architecture.architectureLabels)
      ? architecture.architectureLabels
      : [],
    detected: detectedArchitecture,
    evidence: Array.isArray(architecture.evidence) ? architecture.evidence : [],
  };

  const metrics = analysis.metrics || {};
  METRICS = METRICS.map((metric) => {
    if (metric.label === "Issues Detected") return { ...metric, value: String(metrics.issues ?? ISSUES.length), note: "From latest repository scan" };
    if (metric.label === "Critical Issues") return { ...metric, value: String(metrics.critical ?? SEVERITY_COUNTS.critical), note: metrics.critical ? "Needs immediate review" : "None detected" };
    if (metric.label === "Security Findings") {
      const total = metrics.securityFindings ?? Object.values(SEVERITY_COUNTS).reduce((a, b) => a + b, 0);
      return { ...metric, value: String(total), note: `${SEVERITY_COUNTS.critical} critical · ${SEVERITY_COUNTS.high} high` };
    }
    if (metric.label === "Cloud Resources") {
      const resources = Array.isArray(detectedArchitecture.cloudResources) ? detectedArchitecture.cloudResources : [];
      return {
        ...metric,
        value: String(metrics.cloudResourceCount ?? resources.length),
        note: resources.length ? "Detected from repository analysis" : "No cloud resources detected",
      };
    }
    return metric;
  });

  const now = new Date();
  if(HISTORY_REPO !== REPO.fullName) ANALYSIS_HISTORY = [];
  HISTORY_REPO = REPO.fullName;
  ANALYSIS_HISTORY = [{
    date: now.toLocaleString(),
    score: HEALTH.overall,
    issues: ISSUES.length,
    duration: REPO.analysisDuration,
  }, ...ANALYSIS_HISTORY].slice(0, 20);

  ACTIVITY = [
    { time: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), label: "Repository analyzed", status: "done" },
    { time: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), label: `${REPOSITORY_FILES.length} repository files scanned`, status: "done" },
  ];
}

function applyRepositoryData(data) {
  const repository = data?.repository || {};
  REPO = {
    ...REPO,
    name: repository.name || "Unknown repository",
    fullName: repository.fullName || repository.name || "Unknown repository",
    url: repository.url || "",
    branch: repository.branch || "main",
    lastCommitMsg: data?.commits?.[0]?.message || "No commits found",
    analysisCommitSha: repository.analysisCommitSha || "",
    commitHash: repository.analysisCommitSha?.slice(0,7) || data?.commits?.[0]?.hash || "",
    commitAuthor: data?.commits?.[0]?.author || repository.owner || "Unknown",
    lastAnalyzed: "just now",
    analysisDuration: Number.isFinite(data?.scanDurationMs) && data.scanDurationMs >= 0
      ? `${(data.scanDurationMs / 1000).toFixed(2)}s` : "—",
  };

  LANGUAGES = Array.isArray(data?.languages) ? data.languages : [];
  CONTRIBUTORS = Array.isArray(data?.contributors) ? data.contributors : [];
  COMMITS = Array.isArray(data?.commits) ? data.commits.map((commit) => ({
    hash: commit.hash || (commit.sha ? commit.sha.slice(0, 7) : ""),
    message: commit.message || "No commit message",
    author: commit.author || "Unknown",
    time: commit.date ? new Date(commit.date).toLocaleString() : "—",
    url: commit.url || "",
  })) : [];
  REPOSITORY_FILES = Array.isArray(data?.files) ? data.files : [];

  const totalFiles = data?.fileCount ?? REPOSITORY_FILES.length;
  METRICS = METRICS.map((metric) =>
    metric.label === "Total Files"
      ? { ...metric, value: String(totalFiles), note: `Across ${LANGUAGES.length} languages` }
      : metric
  );
}

let revision = 0;
const subscribers = new Set();
export function subscribeRepository(listener) {
  subscribers.add(listener);
  return () => subscribers.delete(listener);
}
export function getRepositoryRevision() { return revision; }
export function buildRepositoryReport() {
  return { repository: REPO, health: HEALTH, subscores: SUBSCORES, security: SECURITY,
    issues: ISSUES, recommendations: RECOMMENDATIONS, architecture: ARCH,
    files: REPOSITORY_FILES, fileCount: REPOSITORY_FILES.length, languages: LANGUAGES,
    inspectionNote: "File inventory is separate from bounded source inspection; findings are static heuristics, not runtime telemetry." };
}
export function publishRepositoryData(data) {
  if(REPO.fullName!==data?.repository?.fullName){ANALYSIS_HISTORY=[];HISTORY_REPO=data?.repository?.fullName || "";}
  applyRepositoryData(data);
  applyAnalysisData(data.analysis);
  revision += 1;
  subscribers.forEach(listener => listener());
}
export { REPO, HEALTH, SUBSCORES, METRICS, SEVERITY_COUNTS, ISSUES, ARCH, SECURITY, RECOMMENDATIONS, ACTIVITY, CONTRIBUTORS, COMMITS, LANGUAGES, REPOSITORY_FILES, ANALYSIS_STEPS, ANALYSIS_HISTORY };
