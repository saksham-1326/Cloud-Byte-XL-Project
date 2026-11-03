import React, { useState } from "react";
import {
  LayoutDashboard, GitBranch, ScanSearch, AlertTriangle, Cloud, Boxes, Container,
  Workflow, ShieldAlert, Lightbulb, FileBarChart2, Settings, HelpCircle, User,
  ChevronLeft, ChevronRight, Bell, RefreshCw, ExternalLink, Check, X,
  Clock, Circle, CheckCircle2, AlertCircle, AlertOctagon, ChevronDown,
  Server, Database, Layers, Code2, FileCode2, Package, Files, TrendingUp,
  TrendingDown, Minus, ArrowRight, Loader2, Plug, MapPin, GitCommit,
  FolderTree, Download,
} from "lucide-react";
import {
  ResponsiveContainer, RadialBarChart, RadialBar, PieChart, Pie, Cell, BarChart,
  Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid,
} from "recharts";

/* ============================== ICONS ============================== */

function Github({ className = "h-4 w-4" }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

/* ============================== MOCK DATA ============================== */

let REPO = {
  name: "cloud-bytexl-project",
  fullName: "acme-labs/cloud-bytexl-project",
  url: "github.com/acme-labs/cloud-bytexl-project",
  branch: "main",
  lastCommitMsg: "Refactor RDS connection pooling and retry logic",
  commitHash: "a3f9c21",
  commitAuthor: "Saksham Sharma",
  lastAnalyzed: "2 minutes ago",
  analysisDuration: "48s",
};

let HEALTH = { overall: 82, status: "Good — Improvements Recommended" };

let SUBSCORES = [
  { label: "Code Quality", value: 88, tone: "emerald" },
  { label: "Security", value: 71, tone: "amber" },
  { label: "Infrastructure", value: 84, tone: "blue" },
  { label: "CI/CD", value: 92, tone: "emerald" },
  { label: "Configuration", value: 76, tone: "amber" },
];

let METRICS = [
  { label: "Total Files", value: "342", icon: Files, note: "Across 8 languages", trend: null },
  { label: "Issues Detected", value: "17", icon: AlertCircle, note: "+3 since last scan", trend: "up" },
  { label: "Critical Issues", value: "2", icon: AlertOctagon, note: "Needs immediate review", trend: "flat", tone: "critical" },
  { label: "Cloud Resources", value: "0", icon: Cloud, note: "From latest repository analysis", trend: null },
  { label: "Security Findings", value: "5", icon: ShieldAlert, note: "2 critical · 1 high", trend: "up", tone: "warning" },
];

let SEVERITY_COUNTS = { critical: 2, high: 5, medium: 7, low: 3 };

let ISSUES = [
  {
    id: 1, severity: "critical", title: "Publicly accessible AWS security group",
    category: "Cloud Infrastructure", file: "security-group.tf", line: 42,
    snippet: 'ingress {\n  from_port   = 0\n  to_port     = 65535\n  cidr_blocks = ["0.0.0.0/0"]\n}',
    why: "The security group allows unrestricted inbound traffic from any IP address on every port.",
    impact: "Any host on the internet can attempt to connect directly to this resource, significantly increasing exposure to scanning and exploitation.",
    recommendation: "Restrict ingress to the required ports only and limit CIDR blocks to trusted ranges or a bastion host.",
    related: "EC2 · VPC",
  },
  {
    id: 2, severity: "high", title: "Container running with excessive privileges",
    category: "Docker", file: "Dockerfile", line: 18,
    snippet: "USER root\nRUN chmod -R 777 /app",
    why: "The container runs as root and grants world-writable permissions to the application directory.",
    impact: "A compromised process inside the container could gain broader access to the host or escalate privileges further.",
    recommendation: "Create a dedicated non-root user and scope file permissions to what the application actually needs.",
    related: "Docker · Kubernetes Deployment",
  },
  {
    id: 3, severity: "medium", title: "Kubernetes deployment missing resource limits",
    category: "Kubernetes", file: "deployment.yaml", line: 27,
    snippet: "containers:\n  - name: api\n    image: cloud-bytexl/api:latest",
    why: "No CPU or memory limits are defined for this container.",
    impact: "A single pod could consume unbounded node resources, causing noisy-neighbor issues or node-level failures.",
    recommendation: "Add resources.requests and resources.limits sized to the workload's actual profile.",
    related: "Kubernetes · Node Pool",
  },
  {
    id: 4, severity: "medium", title: "GitHub Actions workflow uses an unpinned action",
    category: "CI/CD", file: "deploy.yml", line: 9,
    snippet: "uses: actions/checkout@main",
    why: "Referencing a branch instead of a version tag can pull unreviewed changes into the pipeline.",
    impact: "A future update to the action could silently change build behavior or introduce a supply-chain risk.",
    recommendation: "Pin third-party actions to a specific release tag or commit SHA.",
    related: "GitHub Actions",
  },
  {
    id: 5, severity: "high", title: "RDS instance not encrypted at rest",
    category: "Cloud Infrastructure", file: "rds.tf", line: 15,
    snippet: 'resource "aws_db_instance" "primary" {\n  storage_encrypted = false\n}',
    why: "The primary database instance does not have storage encryption enabled.",
    impact: "Data at rest could be exposed if the underlying storage is ever accessed outside normal channels.",
    recommendation: "Enable storage_encrypted and provide a KMS key, then plan a maintenance window to apply it.",
    related: "RDS",
  },
  {
    id: 6, severity: "low", title: "Unused environment variable in configuration",
    category: "Configuration", file: "config.py", line: 14,
    snippet: 'LEGACY_API_KEY = os.getenv("LEGACY_API_KEY")',
    why: "This variable is no longer referenced anywhere in the codebase.",
    impact: "Minor — increases configuration surface area and can confuse future maintainers.",
    recommendation: "Remove the unused variable and its corresponding secret from the environment.",
    related: "Application Config",
  },
  {
    id: 7, severity: "high", title: "IAM policy grants wildcard resource access",
    category: "Cloud Infrastructure", file: "iam-policy.tf", line: 33,
    snippet: '"Action": "s3:*",\n"Resource": "*"',
    why: "The policy grants full S3 access across all resources rather than the specific buckets in use.",
    impact: "A compromised credential using this role could read or delete data in any bucket in the account.",
    recommendation: "Scope the policy to the specific bucket ARNs the application needs.",
    related: "IAM · S3",
  },
  {
    id: 8, severity: "medium", title: "Health check missing on load balancer target group",
    category: "Cloud Infrastructure", file: "alb.tf", line: 21,
    snippet: 'resource "aws_lb_target_group" "api" {\n  # no health_check block\n}',
    why: "Without a health check, the load balancer cannot detect unhealthy instances.",
    impact: "Traffic may continue routing to failing instances, increasing error rates during partial outages.",
    recommendation: "Define a health_check block with an appropriate path, interval, and threshold.",
    related: "ALB · EC2",
  },
];

let ARCH = {
  title: "Repository Architecture",
  reason: "Architecture is determined from evidence in the connected GitHub repository.",
  assessment: "No cloud resource evidence was detected.",
  provider: "Not detected",
  confidence: 0,
  services: [],
  architectureLabels: [],
  detected: {},
  evidence: [],
};

const TECH_STACK = [
  { name: "Python", category: "Language", icon: Code2 },
  { name: "Flask", category: "Framework", icon: Layers },
  { name: "Docker", category: "Container", icon: Container },
  { name: "Kubernetes", category: "Orchestration", icon: Boxes },
  { name: "Terraform", category: "IaC", icon: FileCode2 },
  { name: "GitHub Actions", category: "CI/CD", icon: Workflow },
  { name: "AWS", category: "Cloud", icon: Cloud },
  { name: "MySQL", category: "Database", icon: Database },
];

const CICD_STAGES = [
  { name: "Build", status: "success" },
  { name: "Tests", status: "success" },
  { name: "Docker Build", status: "success" },
  { name: "Security Scan", status: "warning" },
  { name: "Deployment", status: "success" },
];
const CICD_META = { lastRun: "12 minutes ago", duration: "4m 12s", successRate: 96 };
const CICD_HISTORY = [
  { run: "#128", duration: 252 }, { run: "#129", duration: 244 }, { run: "#130", duration: 268 },
  { run: "#131", duration: 231 }, { run: "#132", duration: 260 }, { run: "#133", duration: 239 },
  { run: "#134", duration: 252 },
];

let SECURITY = { score: 71, findings: { critical: 2, high: 1, medium: 2, low: 4 } };

let RECOMMENDATIONS = [
  {
    id: 1, severity: "critical", title: "Restrict public inbound access on the AWS security group",
    why: "The current configuration allows unrestricted inbound traffic from any address.",
    action: "Limit access to required ports and trusted sources such as a bastion host or VPN range.",
    relatedIssue: 1,
  },
  {
    id: 2, severity: "high", title: "Use a non-root user inside the Docker container",
    why: "Running as root increases the impact of any container compromise.",
    action: "Create a dedicated application user and drop root privileges before the entrypoint runs.",
    relatedIssue: 2,
  },
  {
    id: 3, severity: "medium", title: "Add resource limits to the Kubernetes deployment",
    why: "Containers without limits can consume unbounded node resources.",
    action: "Define CPU and memory requests and limits for every container.",
    relatedIssue: 3,
  },
  {
    id: 4, severity: "medium", title: "Pin GitHub Actions to a fixed version",
    why: "Unpinned actions can introduce unreviewed changes into the pipeline.",
    action: "Reference a release tag or commit SHA instead of a branch name.",
    relatedIssue: 4,
  },
];

let ACTIVITY = [
  { time: "10:42 AM", label: "Repository analyzed", status: "done" },
  { time: "10:39 AM", label: "Terraform infrastructure scanned", status: "done" },
  { time: "10:37 AM", label: "Kubernetes manifests analyzed", status: "done" },
  { time: "10:35 AM", label: "GitHub webhook received", status: "done" },
];

let CONTRIBUTORS = [
  { name: "Priya Nair", commits: 128 }, { name: "Daniel Osei", commits: 94 },
  { name: "Wei Zhang", commits: 61 }, { name: "Sara Kim", commits: 37 },
];
let COMMITS = [
  { hash: "a3f9c21", message: "Refactor RDS connection pooling and retry logic", author: "Priya Nair", time: "2 hours ago" },
  { hash: "7cb14e0", message: "Add health checks to ALB target group", author: "Daniel Osei", time: "1 day ago" },
  { hash: "e02d9aa", message: "Bump base image to python:3.12-slim", author: "Wei Zhang", time: "2 days ago" },
  { hash: "44a1f3c", message: "Tighten IAM policy for deployment role", author: "Priya Nair", time: "3 days ago" },
];
let LANGUAGES = [
  { name: "Python", pct: 54 }, { name: "HCL (Terraform)", pct: 18 }, { name: "YAML", pct: 14 },
  { name: "Dockerfile", pct: 6 }, { name: "Other", pct: 8 },
];
let REPOSITORY_FILES = [];

const ANALYSIS_STEPS = [
  "Repository cloned", "Files discovered", "Source code analyzed", "Docker configuration analyzed",
  "Terraform analysis", "Kubernetes analysis", "Security analysis", "Report generation",
];
let ANALYSIS_HISTORY = [
  { date: "Today, 10:42 AM", score: 82, issues: 17, duration: "48s" },
  { date: "Yesterday, 4:15 PM", score: 79, issues: 21, duration: "52s" },
  { date: "3 days ago, 9:03 AM", score: 79, issues: 19, duration: "51s" },
  { date: "6 days ago, 2:47 PM", score: 74, issues: 24, duration: "55s" },
];

/* ============================== TOKENS / HELPERS ============================== */

const TONE = {
  critical: { text: "text-red-400", bg: "bg-red-500", soft: "bg-red-500/10", border: "border-red-500/30", ring: "ring-red-500/20", hex: "#ef4444" },
  high:     { text: "text-orange-400", bg: "bg-orange-500", soft: "bg-orange-500/10", border: "border-orange-500/30", ring: "ring-orange-500/20", hex: "#fb923c" },
  medium:   { text: "text-amber-400", bg: "bg-amber-500", soft: "bg-amber-500/10", border: "border-amber-500/30", ring: "ring-amber-500/20", hex: "#fbbf24" },
  low:      { text: "text-slate-400", bg: "bg-slate-500", soft: "bg-slate-500/10", border: "border-slate-500/30", ring: "ring-slate-500/20", hex: "#94a3b8" },
  amber:    { text: "text-amber-400", bg: "bg-amber-500", soft: "bg-amber-500/10", border: "border-amber-500/30", hex: "#fbbf24" },
  emerald:  { text: "text-emerald-400", bg: "bg-emerald-500", soft: "bg-emerald-500/10", border: "border-emerald-500/30", hex: "#10b981" },
  blue:     { text: "text-blue-400", bg: "bg-blue-500", soft: "bg-blue-500/10", border: "border-blue-500/30", hex: "#3b82f6" },
  cyan:     { text: "text-cyan-400", bg: "bg-cyan-500", soft: "bg-cyan-500/10", border: "border-cyan-500/30", hex: "#22d3ee" },
};

function scoreTone(v) {
  if (v >= 85) return "emerald";
  if (v >= 70) return "amber";
  return "critical";
}

function SeverityBadge({ severity }) {
  const t = TONE[severity];
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border ${t.border} ${t.soft} px-2 py-0.5 text-xs font-mono font-semibold uppercase tracking-wide ${t.text}`}>
      {severity}
    </span>
  );
}

function Card({ children, className = "", hover = true }) {
  return (
    <div className={`rounded-xl border border-slate-800 bg-slate-900 ${hover ? "transition-colors hover:border-slate-700" : ""} ${className}`}>
      {children}
    </div>
  );
}

function SectionHeader({ eyebrow, title, subtitle, action }) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div>
        {eyebrow && <div className="mb-1 text-xs font-mono uppercase tracking-wider text-slate-500">{eyebrow}</div>}
        <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

function ProgressBar({ value, tone = "blue", trackClass = "bg-slate-800" }) {
  const t = TONE[tone] || TONE.blue;
  return (
    <div className={`h-1.5 w-full overflow-hidden rounded-full ${trackClass}`}>
      <div className={`h-full rounded-full ${t.bg}`} style={{ width: `${value}%` }} />
    </div>
  );
}

function StageStatusIcon({ status, className = "h-4 w-4" }) {
  if (status === "success") return <CheckCircle2 className={`${className} text-emerald-400`} />;
  if (status === "warning") return <AlertTriangle className={`${className} text-amber-400`} />;
  if (status === "running") return <Loader2 className={`${className} animate-spin text-blue-400`} />;
  if (status === "error") return <X className={`${className} text-red-400`} />;
  return <Circle className={`${className} text-slate-600`} />;
}

function TrendTag({ trend }) {
  if (!trend) return null;
  if (trend === "up") return <span className="inline-flex items-center gap-0.5 text-xs font-medium text-amber-400"><TrendingUp className="h-3 w-3" />up</span>;
  if (trend === "down") return <span className="inline-flex items-center gap-0.5 text-xs font-medium text-emerald-400"><TrendingDown className="h-3 w-3" />down</span>;
  return <span className="inline-flex items-center gap-0.5 text-xs font-medium text-slate-500"><Minus className="h-3 w-3" />flat</span>;
}

function Tooltip2({ label, children }) {
  return (
    <div className="group/tip relative flex items-center">
      {children}
      <div className="pointer-events-none absolute left-full ml-2 whitespace-nowrap rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200 opacity-0 shadow-lg transition-opacity group-hover/tip:opacity-100 z-50">
        {label}
      </div>
    </div>
  );
}

/* ============================== SIDEBAR ============================== */

const NAV_ITEMS = [
  { key: "overview", label: "Overview", icon: LayoutDashboard },
  { key: "repository", label: "Repository", icon: GitBranch },
  { key: "analysis", label: "Analysis", icon: ScanSearch },
  { key: "issues", label: "Issues", icon: AlertTriangle },
  { key: "architecture", label: "Architecture", icon: Cloud },
  { key: "kubernetes", label: "Kubernetes", icon: Boxes },
  { key: "docker", label: "Docker", icon: Container },
  { key: "cicd", label: "CI/CD", icon: Workflow },
  { key: "security", label: "Security", icon: ShieldAlert },
  { key: "recommendations", label: "Recommendations", icon: Lightbulb },
  { key: "reports", label: "Reports", icon: FileBarChart2 },
];

function Sidebar({ collapsed, setCollapsed, page, setPage }) {
  return (
    <aside className={`fixed inset-y-0 left-0 z-40 hidden flex-col border-r border-slate-800 bg-slate-900 transition-all duration-200 sm:flex ${collapsed ? "w-16" : "w-64"}`}>
      <div className={`flex h-16 items-center border-b border-slate-800 ${collapsed ? "justify-center px-0" : "justify-between px-4"}`}>
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <Cloud className="h-4 w-4 text-white" strokeWidth={2.25} />
            </div>
            <span className="text-sm font-semibold tracking-tight text-slate-100">Cloud-ByteXL</span>
          </div>
        )}
        {collapsed && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <Cloud className="h-4 w-4 text-white" strokeWidth={2.25} />
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3">
        {NAV_ITEMS.map((item) => {
          const active = page === item.key;
          const ItemIcon = item.icon;
          const btn = (
            <button
              key={item.key}
              onClick={() => setPage(item.key)}
              className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors ${
                collapsed ? "justify-center" : ""
              } ${
                active
                  ? "bg-blue-500/10 text-blue-400 ring-1 ring-inset ring-blue-500/30"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <ItemIcon className="h-4 w-4 shrink-0" strokeWidth={2} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
          return collapsed ? <Tooltip2 key={item.key} label={item.label}>{btn}</Tooltip2> : btn;
        })}
      </nav>

      <div className="space-y-0.5 border-t border-slate-800 px-2 py-3">
        {[
          { icon: Settings, label: "Settings" },
          { icon: HelpCircle, label: "Help" },
        ].map((it) => {
          const ItemIcon = it.icon;
          const content = (
            <button className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-sm text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200 ${collapsed ? "justify-center" : ""}`}>
              <ItemIcon className="h-4 w-4 shrink-0" strokeWidth={2} />
              {!collapsed && <span>{it.label}</span>}
            </button>
          );
          return collapsed ? <Tooltip2 key={it.label} label={it.label}>{content}</Tooltip2> : <div key={it.label}>{content}</div>;
        })}
        <div className={`mt-1 flex items-center gap-3 rounded-lg px-2.5 py-2 ${collapsed ? "justify-center" : ""}`}>
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-semibold text-slate-200">SS</div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="truncate text-sm text-slate-200">Saksham Sharma</div>
              <div className="truncate text-xs text-slate-500">DevOps Engineer</div>
            </div>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`mt-1 flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs text-slate-500 transition-colors hover:bg-slate-800 hover:text-slate-300 ${collapsed ? "justify-center" : ""}`}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <><ChevronLeft className="h-4 w-4" /> Collapse</>}
        </button>
      </div>
    </aside>
  );
}

/* ============================== NAVBAR ============================== */

function Navbar({ collapsed, onAnalyze, analyzing, repoConnected, onConnectRepo, notifOpen, setNotifOpen, profileOpen, setProfileOpen }) {
  return (
    <header className={`fixed right-0 top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/95 px-4 transition-all duration-200 sm:px-6 ${collapsed ? "sm:left-16" : "sm:left-64"} left-0`}>
      <div className="flex min-w-0 items-center gap-3">
        {repoConnected ? (
          <>
            <button className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-800/60 px-3 py-1.5 text-sm text-slate-200 hover:border-slate-700">
              <Github className="h-3.5 w-3.5 text-slate-400" />
              <span className="max-w-36 truncate font-medium sm:max-w-xs">{REPO.name}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
            </button>
            <span className="hidden items-center gap-1.5 rounded-md bg-slate-800 px-2 py-1 text-xs font-mono text-slate-300 md:inline-flex">
              <GitBranch className="h-3 w-3 text-slate-500" /> {REPO.branch}
            </span>
            <span className="hidden items-center gap-1.5 text-xs text-slate-500 lg:inline-flex">
              <Clock className="h-3 w-3" /> Analyzed {REPO.lastAnalyzed}
            </span>
          </>
        ) : (
          <span className="text-sm text-slate-500">No repository connected</span>
        )}
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <button
          onClick={(e) => { e.stopPropagation(); onConnectRepo(); }}
          className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-blue-500 hover:bg-slate-700"
        >
          <Github className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">{repoConnected ? "Change Repository" : "Connect Repository"}</span>
        </button>
        {repoConnected && (
          <button
            onClick={onAnalyze}
            disabled={analyzing}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${analyzing ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">{analyzing ? "Analyzing…" : "Analyze Now"}</span>
          </button>
        )}
        <div className="relative">
          <button onClick={() => { setNotifOpen(!notifOpen); setProfileOpen(false); }} className="relative flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-200">
            <Bell className="h-4 w-4" />
            <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-red-500" />
          </button>
          {notifOpen && (
            <div className="absolute right-0 top-10 w-72 rounded-lg border border-slate-800 bg-slate-900 p-2 shadow-xl">
              <div className="px-2 py-1.5 text-xs font-mono uppercase tracking-wide text-slate-500">Notifications</div>
              {[
                { t: "2 new critical findings in Terraform", time: "2m ago" },
                { t: "Security scan flagged 1 issue", time: "12m ago" },
                { t: "Deployment pipeline succeeded", time: "1h ago" },
              ].map((n, i) => (
                <div key={i} className="rounded-md px-2 py-2 text-sm hover:bg-slate-800">
                  <div className="text-slate-200">{n.t}</div>
                  <div className="text-xs text-slate-500">{n.time}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="relative">
          <button onClick={() => { setProfileOpen(!profileOpen); setNotifOpen(false); }} className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-700 text-xs font-semibold text-slate-200 hover:ring-2 hover:ring-slate-600">
            SS
          </button>
          {profileOpen && (
            <div className="absolute right-0 top-10 w-48 rounded-lg border border-slate-800 bg-slate-900 p-1 shadow-xl">
              {["Profile", "Team settings", "Sign out"].map((it) => (
                <button key={it} className="w-full rounded-md px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-800">{it}</button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

/* ============================== ARCHITECTURE DIAGRAM ============================== */

function architectureIcon(label) {
  const value = label.toLowerCase();
  if (value.includes("docker")) return Container;
  if (value.includes("kubernetes")) return Boxes;
  if (value.includes("helm")) return Package;
  if (value.includes("terraform")) return FileCode2;
  if (value.includes("cloudformation") || value.includes("aws")) return Cloud;
  if (value.includes("azure")) return Cloud;
  if (value.includes("gcp") || value.includes("google")) return Cloud;
  if (value.includes("github actions") || value.includes("jenkins") || value.includes("ci/cd")) return Workflow;
  if (value.includes("node.js") || value.includes("npm") || value.includes("yarn")) return Code2;
  if (value.includes("python") || value.includes("java") || value.includes("rust") || value.includes("go modules")) return Code2;
  if (value.includes("database") || value.includes("rds")) return Database;
  return FileCode2;
}

function buildArchitectureGraph() {
  const nodes = [];
  const edges = [];
  const labels = Array.isArray(ARCH.architectureLabels) ? ARCH.architectureLabels : [];
  const detected = ARCH.detected || {};
  const resources = Array.isArray(ARCH.services) ? ARCH.services : [];

  nodes.push({
    id: "github",
    label: REPO.name || "GitHub Repository",
    icon: Github,
    desc: "Connected GitHub repository — the source of truth for the detected architecture.",
  });

  const addNode = (id, label, desc) => {
    if (nodes.some((node) => node.id === id)) return;
    nodes.push({ id, label, icon: architectureIcon(label), desc });
  };

  const labelRules = [
    ["GitHub Actions CI/CD", "github-actions", "GitHub Actions", "CI/CD workflow files were found under .github/workflows/."],
    ["GitLab CI/CD", "gitlab-ci", "GitLab CI/CD", "GitLab CI configuration was found in the repository."],
    ["Jenkins Pipeline", "jenkins", "Jenkins", "A Jenkinsfile was found in the repository."],
    ["Azure DevOps", "azure-devops", "Azure DevOps", "An Azure Pipelines configuration was found."],
    ["Infrastructure as Code (Terraform)", "terraform", "Terraform", "Terraform files or a terraform directory were found."],
    ["AWS CloudFormation", "cloudformation", "AWS CloudFormation", "cloudformation.yaml was found."],
    ["Serverless Framework", "serverless", "Serverless Framework", "serverless.yml was found."],
    ["Multi-container Orchestration", "compose", "Docker Compose", "A Docker Compose configuration was found."],
    ["Containerized (Docker) Deployment", "docker", "Docker", "A Dockerfile was found in the repository."],
    ["Kubernetes Native Manifests", "kubernetes", "Kubernetes", "Kubernetes deployment, service, or ingress manifests were found."],
    ["Helm Charts Management", "helm", "Helm", "Helm chart management files were found."],
    ["Node.js / NPM Ecosystem", "nodejs", "Node.js / NPM", "package.json was found."],
    ["Node.js / Yarn Ecosystem", "yarn", "Node.js / Yarn", "yarn.lock was found."],
    ["Python Ecosystem", "python", "Python", "Python project metadata was found."],
    ["Java Maven Build", "maven", "Java Maven", "pom.xml was found."],
    ["Java Gradle Build", "gradle", "Java Gradle", "Gradle build configuration was found."],
    ["Rust / Cargo", "rust", "Rust / Cargo", "Cargo.toml was found."],
    ["Go Modules", "go", "Go Modules", "go.mod was found."],
    ["Ruby Bundler", "ruby", "Ruby Bundler", "Gemfile was found."],
    ["PHP Composer", "php", "PHP Composer", "composer.json was found."],
    [".NET / C# Project", "dotnet", ".NET / C#", "A .csproj project file was found."],
    ["Angular Frontend", "angular", "Angular", "angular.json was found."],
    ["Next.js React Framework", "nextjs", "Next.js", "next.config.js was found."],
    ["Nuxt.js Vue Framework", "nuxtjs", "Nuxt.js", "nuxt.config.js was found."],
    ["Flutter / Dart", "flutter", "Flutter / Dart", "pubspec.yaml was found."],
    ["iOS CocoaPods", "cocoapods", "iOS CocoaPods", "Podfile was found."],
    ["ESLint Linting", "eslint", "ESLint", ".eslintrc.js was found."],
    ["Jest Testing", "jest", "Jest", "jest.config.js was found."],
    ["Pytest Testing", "pytest", "Pytest", "pytest.ini was found."],
  ];

  labelRules.forEach(([trigger, id, label, desc]) => {
    if (labels.includes(trigger)) addNode(id, label, desc);
  });

  const providerNames = Array.isArray(detected.cloudProviders) ? detected.cloudProviders : [];
  providerNames.forEach((providerName) => {
    addNode(`provider-${providerName.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`, providerName, `Provider-specific evidence for ${providerName} was detected.`);
  });

  resources.slice(0, 8).forEach((resource, index) => {
    addNode(`resource-${index}`, resource, "Provider-specific cloud resource evidence was detected in repository configuration.");
  });

  const order = [
    "github-actions", "gitlab-ci", "jenkins", "azure-devops", "terraform",
    "cloudformation", "serverless", "compose", "docker", "kubernetes", "helm",
    "nodejs", "yarn", "python", "maven", "gradle", "rust", "go", "ruby",
    "php", "dotnet", "angular", "nextjs", "nuxtjs", "flutter", "cocoapods",
    "eslint", "jest", "pytest",
  ];

  const ordered = [
    nodes[0],
    ...order.map((id) => nodes.find((node) => node.id === id)).filter(Boolean),
    ...nodes.slice(1).filter((node) => !order.includes(node.id)),
  ];

  ordered.forEach((node, index) => {
    node.x = 305;
    node.y = 12 + index * 76;
    node.w = 190;
    node.h = 54;
    if (index > 0) edges.push({ from: ordered[index - 1].id, to: node.id });
  });

  if (ordered.length === 1) {
    const application = {
      id: "application",
      label: "Application / Source",
      icon: FileCode2,
      x: 305,
      y: 88,
      w: 190,
      h: 54,
      desc: "No known deployment or infrastructure architecture was detected from the repository files.",
    };
    ordered.push(application);
    edges.push({ from: "github", to: "application" });
  }

  return {
    nodes: ordered,
    edges,
    width: 800,
    height: Math.max(180, ordered.length * 76 + 30),
  };
}

function elbowPath(a, b) {
  const ax = a.x + a.w / 2, ay = a.y + a.h;
  const bx = b.x + b.w / 2, by = b.y;
  if (ax === bx) return `M ${ax} ${ay} L ${bx} ${by}`;
  const midY = ay + (by - ay) / 2;
  return `M ${ax} ${ay} L ${ax} ${midY} L ${bx} ${midY} L ${bx} ${by}`;
}

function ArchitectureDiagram({ full = false, onNodeClick, activeNode }) {
  const graph = buildArchitectureGraph();
  const W = graph.width;
  const H = graph.height;

  return (
    <div className="overflow-x-auto">
      <div className="relative mx-auto" style={{ width: W, height: H }}>
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="absolute inset-0">
          {graph.edges.map((edge, index) => {
            const a = graph.nodes.find((node) => node.id === edge.from);
            const b = graph.nodes.find((node) => node.id === edge.to);
            if (!a || !b) return null;
            const d = elbowPath(a, b);
            return (
              <g key={`${edge.from}-${edge.to}-${index}`}>
                <path d={d} fill="none" stroke="#1e293b" strokeWidth="2" />
                <path d={d} fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 5" opacity="0.55" />
                <circle r="3" fill="#22d3ee">
                  <animateMotion dur={`${2.4 + index * 0.2}s`} repeatCount="indefinite" path={d} />
                </circle>
              </g>
            );
          })}
        </svg>

        {graph.nodes.map((node) => {
          const NodeIcon = node.icon;
          const active = activeNode === node.id;
          return (
            <button
              key={node.id}
              onClick={() => onNodeClick && onNodeClick(node.id)}
              style={{ left: node.x, top: node.y, width: node.w, height: node.h }}
              className={`absolute flex items-center gap-2.5 rounded-lg border bg-slate-900 px-3 text-left transition-all ${
                active
                  ? "border-cyan-400 ring-2 ring-cyan-400/30"
                  : "border-slate-700 hover:border-blue-500/60 hover:bg-slate-800/80"
              } ${full ? "cursor-pointer" : "cursor-default"}`}
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-slate-800">
                <NodeIcon className="h-4 w-4 text-blue-400" strokeWidth={2} />
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-slate-100">{node.label}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ArchitectureSidePanel({ onViewFull }) {
  return (
    <Card className="p-5">
      <div className="mb-2 text-xs font-mono uppercase tracking-wide text-slate-500">Detected Architecture</div>
      {ARCH.architectureLabels.length === 0 ? (
        <p className="mb-5 text-sm text-slate-500">No known architectural files detected.</p>
      ) : (
        <div className="mb-5 space-y-2">
          {ARCH.architectureLabels.map((label) => (
            <div
              key={label}
              className="flex items-start gap-2 rounded-lg border border-slate-800 bg-slate-800/40 px-3 py-2 text-sm text-slate-200"
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              <span>{label}</span>
            </div>
          ))}
        </div>
      )}

      <div className="mb-2 text-xs font-mono uppercase tracking-wide text-slate-500">Detected Cloud Provider</div>
      <div className="mb-2 flex items-center gap-2">
        <Cloud className="h-5 w-5 text-amber-400" />
        <span className="text-base font-semibold text-slate-100">{ARCH.provider}</span>
      </div>
      <p className="mb-5 text-xs leading-relaxed text-slate-500">{ARCH.assessment}</p>

      <div className="mb-2 text-xs font-mono uppercase tracking-wide text-slate-500">Detected Cloud Resources</div>
      {ARCH.services.length === 0 ? (
        <p className="mb-5 text-sm text-slate-500">No provider-specific cloud resources detected.</p>
      ) : (
        <div className="mb-5 flex flex-wrap gap-1.5">
          {ARCH.services.map((service) => (
            <span key={service} className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs font-mono text-slate-300">
              {service}
            </span>
          ))}
        </div>
      )}

      <div className="mb-2 flex items-center justify-between text-xs font-mono uppercase tracking-wide text-slate-500">
        <span>Architecture Confidence</span><span className="text-slate-300">{ARCH.confidence}%</span>
      </div>
      <ProgressBar value={ARCH.confidence} tone="blue" />
      <button onClick={onViewFull} className="mt-5 flex w-full items-center justify-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 py-2 text-sm font-medium text-slate-200 hover:border-slate-600 hover:bg-slate-700">
        View Full Architecture <ArrowRight className="h-3.5 w-3.5" />
      </button>
    </Card>
  );
}

/* ============================== OVERVIEW WIDGETS ============================== */

function RepoInfoBar() {
  const fields = [
    { label: "Repository", value: REPO.name, icon: Github },
    { label: "GitHub URL", value: REPO.url, icon: ExternalLink },
    { label: "Branch", value: REPO.branch, icon: GitBranch },
    { label: "Last Commit", value: REPO.lastCommitMsg, icon: GitCommit },
    { label: "Commit Author", value: REPO.commitAuthor, icon: User },
    { label: "Last Analysis", value: REPO.lastAnalyzed, icon: Clock },
    { label: "Analysis Duration", value: REPO.analysisDuration, icon: ScanSearch },
  ];
  return (
    <Card className="p-5">
      <div className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-4">
        {fields.map((f) => (
          <div key={f.label} className="min-w-0">
            <div className="mb-1 flex items-center gap-1.5 text-xs font-mono uppercase tracking-wide text-slate-500">
              <f.icon className="h-3 w-3" /> {f.label}
            </div>
            <div className="truncate text-sm text-slate-200" title={f.value}>{f.value}</div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function HealthScore() {
  const tone = scoreTone(HEALTH.overall);
  const data = [{ name: "health", value: HEALTH.overall, fill: TONE[tone].hex }];
  return (
    <Card className="p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div className="text-xs font-mono uppercase tracking-wide text-slate-500">Project Health</div>
          <h2 className="mt-1 text-lg font-semibold text-slate-100">Overall Score</h2>
        </div>
        <span className={`rounded-md border px-2.5 py-1 text-xs font-medium ${TONE[tone].border} ${TONE[tone].soft} ${TONE[tone].text}`}>
          {HEALTH.status}
        </span>
      </div>
      <div className="grid grid-cols-1 items-center gap-6 md:grid-cols-[220px_1fr]">
        <div className="relative mx-auto h-52 w-52 md:col-span-1">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart innerRadius="78%" outerRadius="100%" data={data} startAngle={90} endAngle={-270} barSize={14}>
              <RadialBar dataKey="value" background={{ fill: "#1e293b" }} cornerRadius={20} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-mono text-4xl font-bold text-slate-100">{HEALTH.overall}</span>
            <span className="text-xs text-slate-500">out of 100</span>
          </div>
        </div>
        <div className="space-y-3.5 md:col-span-2">
          {SUBSCORES.map((s) => (
            <div key={s.label}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-slate-300">{s.label}</span>
                <span className="font-mono text-slate-200">{s.value}</span>
              </div>
              <ProgressBar value={s.value} tone={s.tone} />
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function MetricCards({ onCloudResourcesClick }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {METRICS.map((m) => {
        const MIcon = m.icon;
        const toneCls = m.tone === "critical" ? "text-red-400" : m.tone === "warning" ? "text-amber-400" : "text-blue-400";
        const isCloudResources = m.label === "Cloud Resources";

        const card = (
          <Card className="h-full p-4 transition hover:border-cyan-500/50 hover:bg-slate-900">
            <div className="mb-3 flex items-center justify-between">
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 ${toneCls}`}>
                <MIcon className="h-4 w-4" strokeWidth={2} />
              </div>
              <TrendTag trend={m.trend} />
            </div>
            <div className="font-mono text-2xl font-bold text-slate-100">{m.value}</div>
            <div className="mt-0.5 text-xs text-slate-500">{m.label}</div>
            <div className="mt-1.5 text-xs text-slate-600">{m.note}</div>
            {isCloudResources && <div className="mt-3 text-xs font-medium text-cyan-400">Click to view resources →</div>}
          </Card>
        );

        return isCloudResources ? (
          <button key={m.label} type="button" onClick={onCloudResourcesClick} className="text-left" aria-label="View detected cloud resources">
            {card}
          </button>
        ) : (
          <div key={m.label}>{card}</div>
        );
      })}
    </div>
  );
}

function IssuesOverview({ onViewAll, onSelectIssue }) {
  const donutData = [
    { name: "Critical", value: SEVERITY_COUNTS.critical, fill: TONE.critical.hex },
    { name: "High", value: SEVERITY_COUNTS.high, fill: TONE.high.hex },
    { name: "Medium", value: SEVERITY_COUNTS.medium, fill: TONE.medium.hex },
    { name: "Low", value: SEVERITY_COUNTS.low, fill: TONE.low.hex },
  ];
  return (
    <Card className="p-5">
      <SectionHeader
        title="Issues Overview"
        subtitle="Findings detected across source code, infrastructure, and CI/CD configuration."
        action={<button onClick={onViewAll} className="text-sm font-medium text-blue-400 hover:text-blue-300">View All Issues →</button>}
      />
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="relative mx-auto h-40 w-40 md:col-span-1">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={donutData} dataKey="value" innerRadius={48} outerRadius={68} paddingAngle={3} stroke="none">
                {donutData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-mono text-2xl font-bold text-slate-100">{ISSUES.length}</span>
            <span className="text-xs text-slate-500">total issues</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 md:col-span-2">
          {Object.entries(SEVERITY_COUNTS).map(([sev, count]) => (
            <div key={sev} className={`rounded-lg border ${TONE[sev].border} ${TONE[sev].soft} p-3`}>
              <div className="flex items-center justify-between">
                <SeverityBadge severity={sev} />
                <span className={`font-mono text-xl font-bold ${TONE[sev].text}`}>{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-5 divide-y divide-slate-800 border-t border-slate-800">
        {ISSUES.slice(0, 3).map((iss) => (
          <button key={iss.id} onClick={() => onSelectIssue(iss)} className="flex w-full items-start gap-3 py-3 text-left hover:bg-slate-800/40 rounded-lg px-2 -mx-2">
            <SeverityBadge severity={iss.severity} />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-slate-200">{iss.title}</div>
              <div className="mt-0.5 truncate font-mono text-xs text-slate-500">{iss.category} · {iss.file}:{iss.line}</div>
            </div>
            <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-slate-600" />
          </button>
        ))}
      </div>
    </Card>
  );
}

function TechStackGrid() {
  return (
    <Card className="p-5">
      <SectionHeader title="Technology Stack" subtitle="Technologies detected across the repository." />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {TECH_STACK.map((t) => (
          <div key={t.name} className="flex items-center gap-2.5 rounded-lg border border-slate-800 bg-slate-800/40 px-3 py-2.5">
            <t.icon className="h-4 w-4 shrink-0 text-cyan-400" />
            <div className="min-w-0">
              <div className="truncate text-sm text-slate-200">{t.name}</div>
              <div className="truncate text-xs text-slate-500">{t.category}</div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function CICDPreview({ onOpenPage }) {
  return (
    <Card className="p-5">
      <SectionHeader
        title="CI/CD Pipeline"
        subtitle={`Last run ${CICD_META.lastRun} · ${CICD_META.duration}`}
        action={<button onClick={onOpenPage} className="text-sm font-medium text-blue-400 hover:text-blue-300">Details →</button>}
      />
      <div className="flex flex-wrap items-center gap-2">
        {CICD_STAGES.map((s, i) => (
          <React.Fragment key={s.name}>
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-800/40 px-3 py-2">
              <StageStatusIcon status={s.status} />
              <span className="text-sm text-slate-200">{s.name}</span>
            </div>
            {i < CICD_STAGES.length - 1 && <ArrowRight className="h-3.5 w-3.5 text-slate-700" />}
          </React.Fragment>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-6 text-sm text-slate-400">
        <span>Success rate: <span className="font-mono text-slate-200">{CICD_META.successRate}%</span></span>
      </div>
    </Card>
  );
}

function SecurityPreview({ onOpenPage }) {
  const tone = scoreTone(SECURITY.score);
  return (
    <Card className="p-5">
      <SectionHeader
        title="Security"
        subtitle="Summary of security findings across infrastructure and containers."
        action={<button onClick={onOpenPage} className="text-sm font-medium text-blue-400 hover:text-blue-300">View Security Report →</button>}
      />
      <div className="flex items-center gap-6">
        <div className="text-center">
          <div className={`font-mono text-3xl font-bold ${TONE[tone].text}`}>{SECURITY.score}</div>
          <div className="text-xs text-slate-500">/ 100</div>
        </div>
        <div className="grid flex-1 grid-cols-2 gap-2 sm:grid-cols-4">
          {Object.entries(SECURITY.findings).map(([sev, count]) => (
            <div key={sev} className="rounded-md border border-slate-800 bg-slate-800/40 px-2.5 py-2 text-center">
              <div className={`font-mono text-lg font-semibold ${TONE[sev].text}`}>{count}</div>
              <div className="text-xs uppercase tracking-wide text-slate-500">{sev}</div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function RecommendationsList({ compact = false }) {
  const list = compact ? RECOMMENDATIONS.slice(0, 3) : RECOMMENDATIONS;
  return (
    <Card className="p-5">
      <SectionHeader eyebrow="AI-Assisted" title="Recommended Actions" subtitle="Review these suggestions and apply the fixes that make sense for your project." />
      <div className="space-y-3">
        {list.map((r, i) => (
          <div key={r.id} className="rounded-lg border border-slate-800 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-slate-800 font-mono text-xs text-slate-400">{i + 1}</div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-slate-100">{r.title}</span>
                  <SeverityBadge severity={r.severity} />
                </div>
                <p className="mt-1.5 text-sm text-slate-400"><span className="text-slate-500">Why it matters — </span>{r.why}</p>
                <p className="mt-1 text-sm text-slate-400"><span className="text-slate-500">Suggested fix — </span>{r.action}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ActivityTimeline() {
  return (
    <Card className="p-5">
      <SectionHeader title="Recent Analysis Activity" />
      <div className="space-y-4">
        {ACTIVITY.map((a, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              {i < ACTIVITY.length - 1 && <div className="my-1 h-6 w-px bg-slate-800" />}
            </div>
            <div className="min-w-0 flex-1 pb-1">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-slate-200">{a.label}</span>
                <span className="shrink-0 font-mono text-xs text-slate-500">{a.time}</span>
              </div>
              <span className="text-xs text-emerald-500">Completed</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ============================== PAGES ============================== */

function OverviewPage({ setPage, onSelectIssue, onCloudResourcesClick }) {
  const [archActive, setArchActive] = useState(null);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Project Overview</h1>
        <p className="mt-1 text-sm text-slate-400">Intelligent analysis of your GitHub repository and cloud infrastructure.</p>
      </div>
      <RepoInfoBar />
      <HealthScore />
      <MetricCards onCloudResourcesClick={onCloudResourcesClick} />
      <IssuesOverview onViewAll={() => setPage("issues")} onSelectIssue={onSelectIssue} />

      <div>
        <SectionHeader eyebrow="Signature" title={ARCH.title} subtitle={ARCH.reason} />
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-4">
          <Card className="p-5 lg:col-span-3">
            <ArchitectureDiagram activeNode={archActive} onNodeClick={setArchActive} />
          </Card>
          <div className="lg:col-span-1">
            <ArchitectureSidePanel onViewFull={() => setPage("architecture")} />
          </div>
        </div>
      </div>

      <TechStackGrid />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <CICDPreview onOpenPage={() => setPage("cicd")} />
        <SecurityPreview onOpenPage={() => setPage("security")} />
      </div>

      <RecommendationsList compact />
      <ActivityTimeline />
    </div>
  );
}

function RepositoryPage() {
  const maxCommit = Math.max(...CONTRIBUTORS.map((c) => c.commits));
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Repository</h1>
        <p className="mt-1 text-sm text-slate-400">Structure, history, and contributors for {REPO.name}.</p>
      </div>
      <RepoInfoBar />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card className="p-5">
          <SectionHeader title="Language Distribution" />
          <div className="space-y-3">
            {LANGUAGES.map((l) => (
              <div key={l.name}>
                <div className="mb-1 flex justify-between text-sm"><span className="text-slate-300">{l.name}</span><span className="font-mono text-slate-400">{l.pct}%</span></div>
                <ProgressBar value={l.pct} tone="blue" />
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-5">
          <SectionHeader title="Contributors" />
          <div className="space-y-3">
            {CONTRIBUTORS.map((c) => (
              <div key={c.name} className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-semibold text-slate-200">
                  {c.name.split(" ").map((p) => p[0]).join("")}
                </div>
                <div className="flex-1">
                  <div className="mb-1 flex justify-between text-sm"><span className="text-slate-300">{c.name}</span><span className="font-mono text-xs text-slate-500">{c.commits} commits</span></div>
                  <ProgressBar value={(c.commits / maxCommit) * 100} tone="cyan" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
      <Card className="p-5">
        <SectionHeader title="File Structure" />
        <div className="space-y-1 font-mono text-sm text-slate-300">
          {REPOSITORY_FILES.length === 0 ? (
            <div className="text-sm text-slate-500">No repository files loaded.</div>
          ) : (
            REPOSITORY_FILES.slice(0, 250).map((file, i) => {
              const path = typeof file === "string" ? file : file.path;
              const depth = Math.max(0, path.split("/").length - 1);
              return (
                <div key={`${path}-${i}`} style={{ paddingLeft: depth * 20 }} className="flex items-center gap-2 rounded px-1.5 py-0.5 hover:bg-slate-800/50">
                  <FolderTree className="h-3.5 w-3.5 text-slate-600" />{path}
                </div>
              );
            })
          )}
        </div>
      </Card>
      <Card className="p-5">
        <SectionHeader title="Recent Commits" />
        <div className="divide-y divide-slate-800">
          {COMMITS.map((c) => (
            <div key={c.hash} className="flex items-center gap-3 py-2.5">
              <GitCommit className="h-4 w-4 shrink-0 text-slate-600" />
              <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-slate-400">{c.hash}</span>
              <span className="min-w-0 flex-1 truncate text-sm text-slate-200">{c.message}</span>
              <span className="shrink-0 text-xs text-slate-500">{c.author} · {c.time}</span>
            </div>
          ))}
        </div>
      </Card>
      <Card className="p-5">
        <SectionHeader title="Analysis History" />
        <div className="divide-y divide-slate-800">
          {ANALYSIS_HISTORY.map((a, i) => (
            <div key={i} className="flex items-center justify-between py-2.5 text-sm">
              <span className="text-slate-300">{a.date}</span>
              <div className="flex items-center gap-5 font-mono text-xs">
                <span className={TONE[scoreTone(a.score)].text}>{a.score}/100</span>
                <span className="text-slate-500">{a.issues} issues</span>
                <span className="text-slate-500">{a.duration}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function AnalysisPage() {
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState(ANALYSIS_STEPS.length);

  const start = () => {
    setRunning(true);
    setStep(0);
    let i = 0;
    const iv = setInterval(() => {
      i += 1;
      setStep(i);
      if (i >= ANALYSIS_STEPS.length) { clearInterval(iv); setTimeout(() => setRunning(false), 500); }
    }, 550);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Analysis</h1>
          <p className="mt-1 text-sm text-slate-400">Run a fresh analysis or review the last completed scan.</p>
        </div>
        <button onClick={start} disabled={running} className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-60">
          <RefreshCw className={`h-4 w-4 ${running ? "animate-spin" : ""}`} /> {running ? "Analyzing…" : "Start Analysis"}
        </button>
      </div>

      <Card className="p-6">
        {running ? (
          <>
            <div className="mb-5 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-200">Analyzing Repository…</span>
              <span className="font-mono text-sm text-slate-400">{Math.round((step / ANALYSIS_STEPS.length) * 100)}%</span>
            </div>
            <ProgressBar value={(step / ANALYSIS_STEPS.length) * 100} tone="blue" />
            <div className="mt-5 space-y-2.5">
              {ANALYSIS_STEPS.map((s, i) => (
                <div key={s} className="flex items-center gap-2.5 text-sm">
                  <StageStatusIcon status={i < step ? "success" : i === step ? "running" : "pending"} />
                  <span className={i <= step ? "text-slate-200" : "text-slate-600"}>{s}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
            <div className="mb-5 flex items-center gap-2 text-emerald-400"><CheckCircle2 className="h-5 w-5" /><span className="text-sm font-medium">Last analysis completed successfully</span></div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {[["Score", `${HEALTH.overall}/100`], ["Issues", String(ISSUES.length)], ["Duration", REPO.analysisDuration], ["Completed", REPO.lastAnalyzed]].map(([k, v]) => (
                <div key={k} className="rounded-lg border border-slate-800 bg-slate-800/40 p-3 text-center">
                  <div className="font-mono text-lg font-semibold text-slate-100">{v}</div>
                  <div className="text-xs text-slate-500">{k}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>
      <Card className="p-5">
        <SectionHeader title="Analysis History" />
        <div className="divide-y divide-slate-800">
          {ANALYSIS_HISTORY.map((a, i) => (
            <div key={i} className="flex items-center justify-between py-2.5 text-sm">
              <span className="text-slate-300">{a.date}</span>
              <div className="flex items-center gap-5 font-mono text-xs">
                <span className={TONE[scoreTone(a.score)].text}>{a.score}/100</span>
                <span className="text-slate-500">{a.issues} issues</span>
                <span className="text-slate-500">{a.duration}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function IssuesPage({ onSelectIssue }) {
  const [filter, setFilter] = useState("all");
  const filtered = filter === "all" ? ISSUES : ISSUES.filter((i) => i.severity === filter);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Issues</h1>
        <p className="mt-1 text-sm text-slate-400">All detected problems across code, infrastructure, containers, and CI/CD.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {["all", "critical", "high", "medium", "low"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-mono uppercase tracking-wide transition-colors ${
              filter === f ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-slate-800 text-slate-400 hover:border-slate-700"
            }`}
          >
            {f} {f !== "all" && `(${SEVERITY_COUNTS[f]})`}
          </button>
        ))}
      </div>
      <Card className="divide-y divide-slate-800 p-2">
        {filtered.map((iss) => (
          <button key={iss.id} onClick={() => onSelectIssue(iss)} className="flex w-full items-start gap-3 rounded-lg p-3 text-left hover:bg-slate-800/40">
            <SeverityBadge severity={iss.severity} />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-slate-200">{iss.title}</div>
              <div className="mt-1 font-mono text-xs text-slate-500">{iss.category} · {iss.file}:{iss.line}</div>
              <div className="mt-1 text-xs text-slate-500 truncate">{iss.why}</div>
            </div>
            <span className="mt-0.5 shrink-0 text-xs font-medium text-blue-400">View Details</span>
          </button>
        ))}
      </Card>
    </div>
  );
}

function ArchitecturePage() {
  const [active, setActive] = useState(null);
  const [showFullArchitecture, setShowFullArchitecture] = useState(false);

  const architectureGraph = buildArchitectureGraph();
  const activeNode = architectureGraph.nodes.find((n) => n.id === active);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
          {ARCH.title}
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          {ARCH.reason} Only evidence from the connected GitHub repository is visualized.
        </p>
      </div>

      <Card className="p-5">
        <SectionHeader
          title="Strict Repository Architecture"
          subtitle="Only exact file/folder matches from the GitHub repository are shown."
        />
        {ARCH.architectureLabels.length === 0 ? (
          <p className="text-sm text-slate-500">No known architectural files detected.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {ARCH.architectureLabels.map((label) => (
              <span key={label} className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
                <CheckCircle2 className="h-4 w-4" />
                {label}
              </span>
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-4">
        <Card className="p-5 lg:col-span-3">
          <ArchitectureDiagram
            full
            activeNode={active}
            onNodeClick={(id) =>
              setActive(id === active ? null : id)
            }
          />
        </Card>

        <div className="space-y-5 lg:col-span-1">
          <ArchitectureSidePanel
            onViewFull={() => setShowFullArchitecture(true)}
          />

          {activeNode && (
            <Card className="p-5">
              <div className="mb-2 flex items-center gap-2">
                <activeNode.icon className="h-4 w-4 text-cyan-400" />
                <span className="text-sm font-semibold text-slate-100">
                  {activeNode.label}
                </span>
              </div>

              <p className="text-sm text-slate-400">
                {activeNode.desc}
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Full Architecture Modal */}
      {showFullArchitecture && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
          onClick={() => setShowFullArchitecture(false)}
        >
          <div
            className="w-full max-w-6xl rounded-xl border border-slate-700 bg-slate-950 p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-100">
                  Full {ARCH.title}
                </h2>
                <p className="mt-1 text-sm text-slate-400">
                  {ARCH.assessment}
                </p>
              </div>

              <button
                onClick={() => setShowFullArchitecture(false)}
                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700"
              >
                Close
              </button>
            </div>

            <div className="flex justify-center overflow-auto rounded-lg border border-slate-800 bg-slate-900 p-4">
              <ArchitectureDiagram
                full
                activeNode={active}
                onNodeClick={(id) =>
                  setActive(id === active ? null : id)
                }
              />
            </div>

            {activeNode && (
              <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900 p-4">
                <div className="flex items-center gap-2">
                  <activeNode.icon className="h-4 w-4 text-cyan-400" />
                  <span className="font-medium text-slate-100">
                    {activeNode.label}
                  </span>
                </div>

                <p className="mt-2 text-sm text-slate-400">
                  {activeNode.desc}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function InfraFindingsPage({ title, subtitle, category, meta }) {
  const items = ISSUES.filter((i) => i.category === category);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">{title}</h1>
        <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {meta.map(([k, v]) => (
          <Card key={k} className="p-4 text-center">
            <div className="font-mono text-xl font-bold text-slate-100">{v}</div>
            <div className="mt-0.5 text-xs text-slate-500">{k}</div>
          </Card>
        ))}
      </div>
      <Card className="p-5">
        <SectionHeader title="Related Findings" subtitle={`Issues detected in ${category.toLowerCase()} configuration.`} />
        {items.length === 0 ? (
          <p className="text-sm text-slate-500">No issues detected in this area.</p>
        ) : (
          <div className="divide-y divide-slate-800">
            {items.map((iss) => (
              <div key={iss.id} className="flex items-start gap-3 py-3">
                <SeverityBadge severity={iss.severity} />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-slate-200">{iss.title}</div>
                  <div className="mt-0.5 font-mono text-xs text-slate-500">{iss.file}:{iss.line}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function CICDPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">CI/CD</h1>
        <p className="mt-1 text-sm text-slate-400">Pipeline stages, run history, and reliability trends.</p>
      </div>
      <Card className="p-6">
        <div className="mb-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center sm:gap-2">
          {CICD_STAGES.map((s, i) => (
            <React.Fragment key={s.name}>
              <div className="flex w-full items-center gap-2.5 rounded-lg border border-slate-800 bg-slate-800/40 px-4 py-3 sm:w-auto">
                <StageStatusIcon status={s.status} className="h-5 w-5" />
                <span className="text-sm font-medium text-slate-200">{s.name}</span>
              </div>
              {i < CICD_STAGES.length - 1 && <ArrowRight className="hidden h-4 w-4 shrink-0 text-slate-700 sm:block" />}
            </React.Fragment>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-4 border-t border-slate-800 pt-5 text-center">
          <div><div className="font-mono text-lg font-semibold text-slate-100">{CICD_META.lastRun}</div><div className="text-xs text-slate-500">Last Run</div></div>
          <div><div className="font-mono text-lg font-semibold text-slate-100">{CICD_META.duration}</div><div className="text-xs text-slate-500">Duration</div></div>
          <div><div className="font-mono text-lg font-semibold text-emerald-400">{CICD_META.successRate}%</div><div className="text-xs text-slate-500">Success Rate</div></div>
        </div>
      </Card>
      <Card className="p-5">
        <SectionHeader title="Pipeline Duration Trend" subtitle="Build duration (seconds) across the last 7 runs." />
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={CICD_HISTORY}>
            <CartesianGrid stroke="#1e293b" vertical={false} />
            <XAxis dataKey="run" stroke="#64748b" fontSize={12} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, fontSize: 12 }} />
            <Line type="monotone" dataKey="duration" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3, fill: "#3b82f6" }} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

function SecurityPage({ onSelectIssue }) {
  const tone = scoreTone(SECURITY.score);
  const barData = Object.entries(SECURITY.findings).map(([sev, count]) => ({ sev, count, fill: TONE[sev].hex }));
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Security</h1>
        <p className="mt-1 text-sm text-slate-400">Security posture across cloud infrastructure, containers, and configuration.</p>
      </div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-4">
        <Card className="flex flex-col items-center justify-center p-6 lg:col-span-1">
          <span className={`font-mono text-4xl font-bold ${TONE[tone].text}`}>{SECURITY.score}</span>
          <span className="mt-1 text-xs text-slate-500">Security Score / 100</span>
        </Card>
        <Card className="p-5 lg:col-span-3">
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={barData} layout="vertical" margin={{ left: 10 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="sev" stroke="#94a3b8" fontSize={12} width={70} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                {barData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <Card className="p-5">
        <SectionHeader title="Top Security Findings" />
        <div className="divide-y divide-slate-800">
          {ISSUES.filter((i) => i.severity === "critical" || i.severity === "high").map((iss) => (
            <button key={iss.id} onClick={() => onSelectIssue(iss)} className="flex w-full items-start gap-3 py-3 text-left hover:bg-slate-800/40 rounded-lg px-2 -mx-2">
              <SeverityBadge severity={iss.severity} />
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-slate-200">{iss.title}</div>
                <div className="mt-0.5 font-mono text-xs text-slate-500">{iss.file}:{iss.line}</div>
              </div>
              <span className="mt-0.5 shrink-0 text-xs font-medium text-blue-400">View Details</span>
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
}

function RecommendationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Recommendations</h1>
        <p className="mt-1 text-sm text-slate-400">Review each suggestion and apply the fix manually — nothing here is changed automatically.</p>
      </div>
      <RecommendationsList />
    </div>
  );
}

function ReportsPage({ onExport }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Reports</h1>
          <p className="mt-1 text-sm text-slate-400">A shareable summary of the latest analysis.</p>
        </div>
        <button onClick={onExport} className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-600">
          <Download className="h-4 w-4" /> Export Report
        </button>
      </div>
      <Card className="p-5">
        <SectionHeader title="Executive Summary" />
        <p className="text-sm leading-relaxed text-slate-400">
          {REPO.name} scored {HEALTH.overall}/100 in the latest analysis, rated "{HEALTH.status}". Of {METRICS.find((m) => m.label === "Total Files")?.value || 0} files scanned,
          {ISSUES.length} issues were detected — {SEVERITY_COUNTS.critical} critical and {SEVERITY_COUNTS.high} high severity.
          Findings and recommendations below are generated from the connected repository scan.
        </p>
      </Card>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <HealthScore />
        <TechStackGrid />
      </div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <SecurityPreview onOpenPage={() => {}} />
        <CICDPreview onOpenPage={() => {}} />
      </div>
      <RecommendationsList />
    </div>
  );
}

/* ============================== MODALS & TOASTS ============================== */

function IssueDetailModal({ issue, onClose, onMarkReviewed, reviewed }) {
  if (!issue) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div style={{ maxHeight: "85vh" }} className="w-full max-w-xl overflow-y-auto rounded-xl border border-slate-800 bg-slate-900 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 flex items-start justify-between gap-4 border-b border-slate-800 bg-slate-900 p-5">
          <div>
            <SeverityBadge severity={issue.severity} />
            <h3 className="mt-2 text-base font-semibold text-slate-100">{issue.title}</h3>
            <div className="mt-1 font-mono text-xs text-slate-500">{issue.category} · {issue.file}:{issue.line}</div>
          </div>
          <button onClick={onClose} className="rounded-md p-1.5 text-slate-500 hover:bg-slate-800 hover:text-slate-300"><X className="h-4 w-4" /></button>
        </div>
        <div className="space-y-4 p-5">
          <div>
            <div className="mb-1.5 text-xs font-mono uppercase tracking-wide text-slate-500">Detected Configuration</div>
            <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-black/40 p-3 font-mono text-xs text-slate-300">{issue.snippet}</pre>
          </div>
          <div>
            <div className="mb-1 text-xs font-mono uppercase tracking-wide text-slate-500">Why This Is a Problem</div>
            <p className="text-sm text-slate-300">{issue.why}</p>
          </div>
          <div>
            <div className="mb-1 text-xs font-mono uppercase tracking-wide text-slate-500">Potential Impact</div>
            <p className="text-sm text-slate-300">{issue.impact}</p>
          </div>
          <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-3">
            <div className="mb-1 text-xs font-mono uppercase tracking-wide text-blue-400">Recommended Solution</div>
            <p className="text-sm text-slate-200">{issue.recommendation}</p>
          </div>
          <div>
            <div className="mb-1 text-xs font-mono uppercase tracking-wide text-slate-500">Related Infrastructure</div>
            <p className="text-sm text-slate-300">{issue.related}</p>
          </div>
        </div>
        <div className="flex items-center justify-end gap-3 border-t border-slate-800 p-4">
          <button className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-600">
            <ExternalLink className="h-3.5 w-3.5" /> View on GitHub
          </button>
          <button
            onClick={() => onMarkReviewed(issue.id)}
            disabled={reviewed}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Check className="h-3.5 w-3.5" /> {reviewed ? "Reviewed" : "Mark as Reviewed"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConnectRepoModal({ open, onClose, onConnect }) {
  const [url, setUrl] = useState("");
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-100">Connect GitHub Repository</h3>
          <button onClick={onClose} className="rounded-md p-1.5 text-slate-500 hover:bg-slate-800 hover:text-slate-300"><X className="h-4 w-4" /></button>
        </div>
        <label className="mb-1.5 block text-xs font-mono uppercase tracking-wide text-slate-500">Repository URL</label>
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5">
          <Github className="h-4 w-4 text-slate-500" />
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="github.com/your-org/your-repo"
            className="w-full bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none"
          />
        </div>
        <button onClick={() => onConnect(url)} className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-500">
          <Plug className="h-4 w-4" /> Connect Repository
        </button>
      </div>
    </div>
  );
}

function EmptyState({ onConnect }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-800 bg-slate-900">
        <Github className="h-7 w-7 text-slate-400" />
      </div>
      <h1 className="text-xl font-semibold text-slate-100">Connect your first GitHub repository</h1>
      <p className="mt-2 max-w-md text-sm text-slate-400">
        Let Cloud-ByteXL analyze your code, infrastructure, containers, Kubernetes configuration, and CI/CD pipeline.
      </p>
      <button onClick={onConnect} className="mt-6 flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-500">
        <Github className="h-4 w-4" /> Connect GitHub Repository
      </button>
    </div>
  );
}

function AnalyzingOverlay({ step }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <div className="mb-5 flex items-center gap-2.5">
          <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
          <span className="text-sm font-medium text-slate-100">Analyzing Repository…</span>
        </div>
        <ProgressBar value={(step / ANALYSIS_STEPS.length) * 100} tone="blue" />
        <div className="mt-5 space-y-2.5">
          {ANALYSIS_STEPS.map((s, i) => (
            <div key={s} className="flex items-center gap-2.5 text-sm">
              <StageStatusIcon status={i < step ? "success" : i === step ? "running" : "pending"} />
              <span className={i <= step ? "text-slate-200" : "text-slate-600"}>{s}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Toasts({ toasts }) {
  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-50 space-y-2">
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto flex items-center gap-2.5 rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-100 shadow-xl">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" /> {t.message}
        </div>
      ))}
    </div>
  );
}

function CloudResourcesModal({ resources, onClose }) {
  const resourceList = Array.isArray(resources) ? resources : [];
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div><h2 className="text-lg font-semibold text-white">Cloud Resources Found</h2><p className="mt-1 text-sm text-slate-400">{resourceList.length} resources detected from the repository analysis</p></div>
          <button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white">✕</button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-6">
          {resourceList.length === 0 ? (
            <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-8 text-center"><Cloud className="mx-auto h-8 w-8 text-slate-600" /><p className="mt-3 text-sm font-medium text-slate-300">No cloud resources detected</p><p className="mt-1 text-xs leading-5 text-slate-500">The repository analysis did not find provider-specific cloud resource definitions.</p></div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">{resourceList.map((resource,index)=>(<div key={`${resource}-${index}`} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"><div className="flex items-start gap-3"><div className="mt-0.5 rounded-lg border border-cyan-500/20 bg-cyan-500/10 p-2"><Cloud className="h-4 w-4 text-cyan-400" /></div><div className="min-w-0"><div className="break-words text-sm font-medium text-slate-200">{resource}</div><div className="mt-1 text-xs text-slate-500">Detected resource</div></div></div></div>))}</div>
          )}
        </div>
        <div className="flex justify-end border-t border-slate-800 px-6 py-4"><button type="button" onClick={onClose} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700">Close</button></div>
      </div>
    </div>
  );
}

/* ============================== APP ============================== */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

function applyAnalysisData(analysis) {
  if (!analysis) return;

  HEALTH = {
    overall: Number(analysis.overall ?? 0),
    status: analysis.status || "Analysis completed",
  };

  SUBSCORES = Array.isArray(analysis.subscores) ? analysis.subscores : SUBSCORES;
  ISSUES = Array.isArray(analysis.issues) ? analysis.issues : [];
  SEVERITY_COUNTS = analysis.severityCounts || { critical: 0, high: 0, medium: 0, low: 0 };
  SECURITY = analysis.security || { score: 100, findings: SEVERITY_COUNTS };
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
  ANALYSIS_HISTORY = [{
    date: now.toLocaleString(),
    score: HEALTH.overall,
    issues: ISSUES.length,
    duration: REPO.analysisDuration,
  }];

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
    commitHash: data?.commits?.[0]?.hash || "",
    commitAuthor: data?.commits?.[0]?.author || repository.owner || "Unknown",
    lastAnalyzed: "just now",
    analysisDuration: "—",
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

export default function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [page, setPage] = useState("overview");
  const [repoConnected, setRepoConnected] = useState(false);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showResourcesModal, setShowResourcesModal] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeStep, setAnalyzeStep] = useState(0);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [reviewedIds, setReviewedIds] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [, setRepoVersion] = useState(0);

  const pushToast = (message) => {
    const id = Date.now();
    setToasts((t) => [...t, { id, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200);
  };

  const runAnalysis = async () => {
    if (!REPO.url) {
      pushToast("Connect a GitHub repository first");
      return;
    }
    await handleConnect(REPO.url);
  };

  const handleConnect = async (url) => {
    const repoUrl = (url || "").trim();
    if (!repoUrl) {
      pushToast("Please enter a GitHub repository URL");
      return;
    }

    setShowConnectModal(false);
    setAnalyzing(true);
    setAnalyzeStep(1);
    pushToast("Connecting to GitHub…");

    try {
      const response = await fetch(`${API_BASE}/api/github/repository`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: repoUrl }),
      });

      const data = await response.json();
      if (!response.ok || data.status !== "SUCCESS") {
        throw new Error(data.message || data.error || "Failed to connect GitHub repository");
      }

      applyRepositoryData(data);
      applyAnalysisData(data.analysis);
      setRepoConnected(true);
      setRepoVersion((v) => v + 1);
      setAnalyzeStep(ANALYSIS_STEPS.length);
      setPage("overview");
      pushToast(`Connected to ${data.repository?.fullName || data.repository?.name}`);
    } catch (error) {
      setRepoConnected(false);
      pushToast(error.message || "Failed to connect GitHub repository");
    } finally {
      setTimeout(() => setAnalyzing(false), 350);
    }
  };

  const handleMarkReviewed = (id) => {
    setReviewedIds((r) => [...r, id]);
    pushToast("Issue marked as reviewed");
  };

  const handleExport = () => {
    pushToast("Report exported to PDF");
  };

  const closeMenus = () => { setNotifOpen(false); setProfileOpen(false); };

  let content;
  if (!repoConnected) {
    content = <EmptyState onConnect={() => setShowConnectModal(true)} />;
  } else {
    switch (page) {
      case "overview": content = <OverviewPage setPage={setPage} onSelectIssue={setSelectedIssue} onCloudResourcesClick={() => setShowResourcesModal(true)} />; break;
      case "repository": content = <RepositoryPage />; break;
      case "analysis": content = <AnalysisPage />; break;
      case "issues": content = <IssuesPage onSelectIssue={setSelectedIssue} />; break;
      case "architecture": content = <ArchitecturePage />; break;
      case "docker": content = (
        <InfraFindingsPage
          title="Docker" subtitle="Container build and runtime configuration detected in the repository." category="Docker"
          meta={[["Images", "3"], ["Dockerfiles", "2"], ["Base Image", "python:3.12-slim"], ["Findings", "1"]]}
        />
      ); break;
      case "kubernetes": content = (
        <InfraFindingsPage
          title="Kubernetes" subtitle="Manifests, deployments, and services discovered in the cluster configuration." category="Kubernetes"
          meta={[["Deployments", "4"], ["Services", "6"], ["Node Pools", "2"], ["Findings", "1"]]}
        />
      ); break;
      case "cicd": content = <CICDPage />; break;
      case "security": content = <SecurityPage onSelectIssue={setSelectedIssue} />; break;
      case "recommendations": content = <RecommendationsPage />; break;
      case "reports": content = <ReportsPage onExport={handleExport} />; break;
      default: content = <OverviewPage setPage={setPage} onSelectIssue={setSelectedIssue} onCloudResourcesClick={() => setShowResourcesModal(true)} />;
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100" onClick={closeMenus}>
      {repoConnected && <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} page={page} setPage={setPage} />}
      {repoConnected && (
        <Navbar
          collapsed={collapsed}
          onAnalyze={runAnalysis}
          analyzing={analyzing}
          repoConnected={repoConnected}
          onConnectRepo={() => setShowConnectModal(true)}
          notifOpen={notifOpen}
          setNotifOpen={setNotifOpen}
          profileOpen={profileOpen}
          setProfileOpen={setProfileOpen}
        />
      )}
      <main className={`transition-all duration-200 ${repoConnected ? (collapsed ? "sm:pl-16" : "sm:pl-64") : ""} ${repoConnected ? "pt-16" : ""}`}>
        <div className={repoConnected ? "mx-auto max-w-7xl p-4 sm:p-6 lg:p-8" : ""}>
          {content}
        </div>
      </main>

      <ConnectRepoModal open={showConnectModal} onClose={() => setShowConnectModal(false)} onConnect={handleConnect} />
      {showResourcesModal && (
        <CloudResourcesModal resources={ARCH.services} onClose={() => setShowResourcesModal(false)} />
      )}
      <IssueDetailModal
        issue={selectedIssue}
        onClose={() => setSelectedIssue(null)}
        onMarkReviewed={handleMarkReviewed}
        reviewed={selectedIssue ? reviewedIds.includes(selectedIssue.id) : false}
      />
      {analyzing && <AnalyzingOverlay step={analyzeStep} />}
      <Toasts toasts={toasts} />
    </div>
  );
}