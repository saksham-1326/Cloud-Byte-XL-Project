import type {IconName} from "./components/Icon";
export type PageId =
  | "overview"
  | "repository"
  | "analysis"
  | "issues"
  | "security"
  | "recommendations"
  | "architecture"
  | "cicd"
  | "docker"
  | "kubernetes"
  | "reports"
  | "ai";

export const destinations: { id: PageId; label: string; icon: IconName; group: string; hint: string }[] = [
  {
    id: "overview",
    label: "Mission Control",
    icon: "command",
    group: "Observe",
    hint: "Unified operational intelligence",
  },
  {
    id: "repository",
    label: "Repository",
    icon: "code",
    group: "Observe",
    hint: "Code and commit intelligence",
  },
  {
    id: "analysis",
    label: "Analysis",
    icon: "scan",
    group: "Observe",
    hint: "Repository scan workflow",
  },
  {
    id: "issues",
    label: "Issues",
    icon: "alert",
    group: "Protect",
    hint: "Investigation workspace",
  },
  {
    id: "security",
    label: "Security",
    icon: "shield",
    group: "Protect",
    hint: "Threat intelligence center",
  },
  {
    id: "recommendations",
    label: "Recommendations",
    icon: "zap",
    group: "Protect",
    hint: "Prioritized remediation",
  },
  {
    id: "architecture",
    label: "Architecture",
    icon: "layers",
    group: "Operate",
    hint: "Infrastructure topology",
  },
  { id: "cicd", label: "CI / CD", icon: "branch", group: "Operate", hint: "Pipeline operations" },
  {
    id: "docker",
    label: "Docker",
    icon: "docker",
    group: "Operate",
    hint: "Container configuration",
  },
  {
    id: "kubernetes",
    label: "Kubernetes",
    icon: "hex",
    group: "Operate",
    hint: "Cluster configuration",
  },
  {
    id: "reports",
    label: "Reports",
    icon: "report",
    group: "Intelligence",
    hint: "Executive and technical output",
  },
  {
    id: "ai",
    label: "AI Intelligence",
    icon: "spark",
    group: "Intelligence",
    hint: "Predictions and root causes",
  },
];

export const pageTitle: Record<PageId, { eyebrow: string; title: string; description: string }> = {
  overview: {
    eyebrow: "AI mission control",
    title: "Operational field",
    description: "Repository evidence, historical delivery, and experimental intelligence in one workspace.",
  },
  repository: {
    eyebrow: "Source intelligence",
    title: "Repository explorer",
    description: "Inspect code structure, commits, languages, and repository-level signals.",
  },
  analysis: {
    eyebrow: "Analysis engine",
    title: "Repository scan",
    description:
      "Run repository analysis across code, dependencies, infrastructure, and delivery.",
  },
  issues: {
    eyebrow: "Investigation",
    title: "Issue command",
    description: "Triage findings with code evidence, ownership, and remediation context.",
  },
  security: {
    eyebrow: "Threat intelligence",
    title: "Security center",
    description: "Understand attack surface, vulnerability paths, and remediation readiness.",
  },
  recommendations: {
    eyebrow: "Remediation",
    title: "Action board",
    description: "Prioritized, repository-aware actions based on recorded findings.",
  },
  architecture: {
    eyebrow: "Infrastructure",
    title: "Architecture field",
    description: "Explore detected services, dependencies, boundaries, and configuration evidence.",
  },
  cicd: {
    eyebrow: "Delivery operations",
    title: "Pipeline control",
    description: "Inspect workflows, stages, logs, and failure evidence across executions.",
  },
  docker: {
    eyebrow: "Container intelligence",
    title: "Docker workspace",
    description:
      "Inspect Dockerfiles, build configuration, image risks, and optimization findings.",
  },
  kubernetes: {
    eyebrow: "Cluster intelligence",
    title: "Kubernetes explorer",
    description: "Review manifests, workloads, policy signals, and configuration evidence.",
  },
  reports: {
    eyebrow: "Reporting",
    title: "Report studio",
    description: "Compose executive and technical exports from recorded analysis data.",
  },
  ai: {
    eyebrow: "AI intelligence",
    title: "Prediction lab",
    description: "Evaluate failure risk, root causes, model performance, and human verification.",
  },
};
