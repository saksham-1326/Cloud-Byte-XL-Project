import MissionControlLanding from "./MissionControlLanding.jsx";
import AIIntelligence from "./AIIntelligence.jsx";
import { API_BASE, requestJson } from "./api.js";
import { REPO, HEALTH, SUBSCORES, METRICS, SEVERITY_COUNTS, ISSUES, ARCH, SECURITY, RECOMMENDATIONS, ACTIVITY, CONTRIBUTORS, COMMITS, LANGUAGES, REPOSITORY_FILES, ANALYSIS_STEPS, ANALYSIS_HISTORY, subscribeRepository, getRepositoryRevision, publishRepositoryData } from "./repositoryData.js";
import { useState, useRef, useEffect, useSyncExternalStore } from "react";
import {
  LayoutDashboard, GitBranch, ScanSearch, AlertTriangle, Cloud, Boxes, Container,
  Workflow, ShieldAlert, Lightbulb, FileBarChart2, User,
  ChevronLeft, ChevronRight, Bell, RefreshCw, ExternalLink, Check, X,
  Clock, Circle, CheckCircle2, AlertCircle, AlertOctagon, ChevronDown,
  Database, Layers, Code2, FileCode2, Package, Files,
  Minus, ArrowRight, Loader2, Plug, GitCommit, Compass, ScanEye, ArrowUp,
  FolderTree, Download, Menu, Sparkles, ShieldCheck, Activity,
} from "lucide-react";
import {
  ResponsiveContainer, PieChart, Pie, Cell, BarChart,
  Bar, XAxis, YAxis, Tooltip,
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

/* ============================== TOKENS / HELPERS ============================== */

const TONE = {
  critical: { text: "text-red-400",     bg: "bg-red-500",     soft: "bg-red-500/10",     border: "border-red-500/30",     ring: "ring-red-500/20",     hex: "#ef4444" },
  high:     { text: "text-orange-400",  bg: "bg-orange-500",  soft: "bg-orange-500/10",  border: "border-orange-500/30",  ring: "ring-orange-500/20",  hex: "#fb923c" },
  medium:   { text: "text-amber-400",   bg: "bg-amber-500",   soft: "bg-amber-500/10",   border: "border-amber-500/30",   ring: "ring-amber-500/20",   hex: "#fbbf24" },
  low:      { text: "text-slate-400",   bg: "bg-slate-500",   soft: "bg-slate-500/10",   border: "border-slate-500/30",   ring: "ring-slate-500/20",   hex: "#94a3b8" },
  amber:    { text: "text-amber-400",   bg: "bg-amber-500",   soft: "bg-amber-500/10",   border: "border-amber-500/30",   hex: "#fbbf24" },
  emerald:  { text: "text-emerald-400", bg: "bg-emerald-500", soft: "bg-emerald-500/10", border: "border-emerald-500/30", hex: "#10b981" },
  blue:     { text: "text-blue-400",    bg: "bg-blue-500",    soft: "bg-blue-500/10",    border: "border-blue-500/30",    hex: "#3b82f6" },
  cyan:     { text: "text-cyan-400",    bg: "bg-cyan-500",    soft: "bg-cyan-500/10",    border: "border-cyan-500/30",    hex: "#22d3ee" },
};

function scoreTone(v) {
  if (v >= 85) return "emerald";
  if (v >= 70) return "amber";
  return "critical";
}

/* ── Primitive components ── */

function SeverityBadge({ severity }) {
  const t = TONE[severity];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] ${t.border} ${t.soft} ${t.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${t.bg} opacity-90`} />
      {severity}
    </span>
  );
}

function ProgressBar({ value, tone = "blue", trackClass = "" }) {
  const t = TONE[tone] || TONE.blue;
  return (
    <div
      className={`h-1 w-full overflow-hidden rounded-full ${trackClass}`}
      style={{ background: "rgba(255,255,255,0.06)" }}
    >
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{
          width: `${value}%`,
          background: `linear-gradient(90deg, ${t.hex} 0%, ${t.hex}cc 100%)`,
          boxShadow: `0 0 8px ${t.hex}35`,
        }}
      />
    </div>
  );
}

/* ============================== SIDEBAR ============================== */

const NAV_ITEMS = [
  { key: "overview",        label: "Overview",        icon: LayoutDashboard },
  { key: "repository",      label: "Repository",      icon: GitBranch },
  { key: "analysis",        label: "Analysis",        icon: ScanSearch },
  { key: "issues",          label: "Issues",          icon: AlertTriangle },
  { key: "architecture",    label: "Architecture",    icon: Cloud },
  { key: "kubernetes",      label: "Kubernetes",      icon: Boxes },
  { key: "docker",          label: "Docker",          icon: Container },
  { key: "cicd",            label: "CI/CD",           icon: Workflow },
  { key: "security",        label: "Security",        icon: ShieldAlert },
  { key: "recommendations", label: "Recommendations", icon: Lightbulb },
  { key: "intelligence", label: "AI Intelligence", icon: Lightbulb },
  { key: "reports",         label: "Reports",         icon: FileBarChart2 },
];

const NAV_GROUPS = [
  { label: "Workspace", keys: ["overview", "repository", "analysis"] },
  { label: "Intelligence", keys: ["issues", "security", "recommendations"] },
  { label: "Infrastructure", keys: ["architecture", "cicd", "docker", "kubernetes"] },
  { label: "Insights", keys: ["intelligence", "reports"] },
];

function Sidebar({ collapsed, setCollapsed, page, setPage, repoConnected }) {
  return <aside className={`workspace-sidebar ${collapsed ? "is-collapsed" : ""}`}>
    <div className="workspace-brand"><div className="brand-mark"><Layers size={20} /></div>{!collapsed && <div><strong>Cloud-ByteXL<span> / </span></strong><small>DEVOPS INTELLIGENCE</small></div>}</div>
    {!collapsed && <div className="workspace-switch"><span className="workspace-avatar">CB</span><div><strong>Engineering workspace</strong><small>Repository intelligence</small></div></div>}
    <nav aria-label="Main navigation">{NAV_GROUPS.map(group => <div className="nav-group" key={group.label}>{!collapsed && <p>{group.label}</p>}{group.keys.map(key => { const item = NAV_ITEMS.find(n => n.key === key); const Icon = item.icon; return <button key={key} title={item.label} aria-current={page === key ? "page" : undefined} className={`workspace-nav-item ${page === key ? "active" : ""}`} onClick={() => setPage(key)}><Icon size={17} />{!collapsed && <><span>{item.label}</span>{key === "issues" && repoConnected && ISSUES.length > 0 && <em>{ISSUES.length}</em>}</>}</button>; })}</div>)}</nav>
    <div className="sidebar-bottom">{!collapsed && <div className="workspace-note"><ScanSearch size={18} /><strong>Clarity from your code.</strong><p>Security, infrastructure, and delivery. One connected view.</p></div>}<button className="workspace-nav-item" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}>{collapsed ? <ChevronRight size={17} /> : <><ChevronLeft size={17} /><span>Collapse sidebar</span></>}</button></div>
  </aside>;
}

/* ============================== NAVBAR ============================== */

function Navbar({ collapsed, onAnalyze, analyzing, repoConnected, onConnectRepo, notifOpen, setNotifOpen, profileOpen, setProfileOpen, onMobileMenuOpen }) {
  return (
    <header
      className={`workspace-navbar fixed right-0 top-0 z-30 flex h-16 items-center justify-between px-4 transition-all duration-300 sm:px-5 ${
        collapsed ? "sm:left-16" : "sm:left-64"
      } left-0`}
      style={{
        background: "rgba(6,9,18,0.88)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}
    >
      {/* Left */}
      <div className="flex min-w-0 flex-1 items-center gap-2.5 pr-2">
        {/* Mobile hamburger — visible below sm breakpoint only */}
        <button
          onClick={onMobileMenuOpen}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted transition-all hover:bg-white/[0.06] hover:text-slate-300 sm:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </button>

        {repoConnected ? (
          <>
            <button
              className="flex min-w-0 items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-slate-200 transition-all hover:bg-white/[0.05]"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--border-default)" }}
              title={REPO.fullName}
              onClick={onConnectRepo}
            >
              <Github className="h-3.5 w-3.5 shrink-0 text-slate-400" />
              <span className="min-w-0 truncate font-medium sm:max-w-[260px]">{REPO.fullName}</span>
              <ChevronDown className="h-3.5 w-3.5 shrink-0 text-faint" />
            </button>
            <span
              className="hidden shrink-0 items-center gap-1.5 rounded-md px-2 py-1 font-mono text-xs text-slate-400 lg:inline-flex"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--border-subtle)" }}
            >
              <GitBranch className="h-3 w-3 text-faint" />
              {REPO.branch}
            </span>
            <span className="hidden shrink-0 items-center gap-1 whitespace-nowrap text-xs text-faint xl:inline-flex">
              <Clock className="h-3 w-3" />
              {REPO.lastAnalyzed}
            </span>
          </>
        ) : (
          <span className="text-sm text-faint">No repository connected</span>
        )}
      </div>

      {/* Right */}
      <div className="flex shrink-0 items-center gap-2">
        <button
          onClick={(e) => { e.stopPropagation(); onConnectRepo(); }}
          className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium text-slate-300 transition-all hover:bg-white/[0.05] hover:text-slate-100"
          style={{ border: "1px solid var(--border-default)" }}
          aria-label={repoConnected ? "Change repository" : "Connect repository"}
        >
          <Github className="h-3.5 w-3.5" />
          <span className="hidden lg:inline">
            {repoConnected ? "Change Repo" : "Connect Repo"}
          </span>
        </button>

        {repoConnected && (
          <button
            onClick={onAnalyze}
            disabled={analyzing}
            className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white transition-all hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ boxShadow: "0 0 14px rgba(59,130,246,0.35)" }}
            aria-label="Re-analyze repository"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${analyzing ? "animate-spin" : ""}`} />
            <span className="hidden lg:inline">{analyzing ? "Analyzing…" : "Analyze Now"}</span>
          </button>
        )}

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={(e) => { e.stopPropagation(); setNotifOpen(!notifOpen); setProfileOpen(false); }}
            className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-all hover:bg-white/[0.06] hover:text-slate-300"
            disabled={!repoConnected}
            aria-label="Notifications"
            aria-expanded={notifOpen}
          >
            <Bell className="h-4 w-4" />
            <span
              className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-blue-400"
              style={{ boxShadow: "0 0 4px rgba(96,165,250,0.8)", border: "1.5px solid #060912" }}
            />
          </button>
          {notifOpen && (
            <div
              className="absolute right-0 top-11 z-50 w-72 max-w-[calc(100vw-2rem)] rounded-xl p-2 shadow-2xl"
              style={{ background: "#0e1525", border: "1px solid var(--border-default)" }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
                Notifications
              </div>
              {[
                SEVERITY_COUNTS.critical > 0 && { t: `${SEVERITY_COUNTS.critical} critical finding${SEVERITY_COUNTS.critical === 1 ? "" : "s"} in the latest analysis`, time: REPO.lastAnalyzed, dot: "bg-red-400" },
                SEVERITY_COUNTS.high > 0 && { t: `${SEVERITY_COUNTS.high} high-severity finding${SEVERITY_COUNTS.high === 1 ? "" : "s"} in the latest analysis`, time: REPO.lastAnalyzed, dot: "bg-amber-400" },
                { t: `${REPO.name} analyzed — ${ISSUES.length} issue${ISSUES.length === 1 ? "" : "s"} found`, time: REPO.lastAnalyzed, dot: "bg-emerald-400" },
              ].filter(Boolean).map((n, i) => (
                <div
                  key={i}
                  className="flex cursor-pointer items-start gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-colors hover:bg-white/[0.04]"
                >
                  <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${n.dot}`} />
                  <div>
                    <div className="text-slate-200">{n.t}</div>
                    <div className="text-xs text-faint">{n.time}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative">
          <button
            onClick={(e) => { e.stopPropagation(); setProfileOpen(!profileOpen); setNotifOpen(false); }}
            className="flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-bold text-white transition-all"
            style={{
              background: "linear-gradient(135deg, #2563eb 0%, #0891b2 100%)",
              boxShadow: "0 0 10px rgba(59,130,246,0.35)",
            }}
            aria-label="Profile menu"
            aria-expanded={profileOpen}
          >
            SS
          </button>
          {profileOpen && (
            <div
              className="absolute right-0 top-11 z-50 w-48 rounded-xl p-1.5 shadow-2xl"
              style={{ background: "#0e1525", border: "1px solid var(--border-default)" }}
              onClick={(e) => e.stopPropagation()}
            >
              {["Profile", "Team settings", "Sign out"].map((it) => (
                <button
                  key={it}
                  className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-400 transition-colors hover:bg-white/[0.05] hover:text-slate-200"
                >
                  {it}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

/* ============================== MOBILE NAV DRAWER ============================== */

function MobileNav({ open, onClose, page, setPage }) {
  if (!open) return null;
  const handleKeys = event => {
    if (event.key === "Escape") onClose();
    if (event.key === "Tab") {
      const controls = [...event.currentTarget.querySelectorAll("button")];
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  };
  return <><div className="mobile-nav-backdrop" onClick={onClose}/><aside className="mobile-nav-panel" role="dialog" aria-modal="true" aria-label="Navigation" onKeyDown={handleKeys}><div className="workspace-brand"><span className="brand-mark"><Layers size={20}/></span><div><strong>Cloud-ByteXL<span> / </span></strong><small>DEVOPS INTELLIGENCE</small></div><button autoFocus aria-label="Close navigation" onClick={onClose}><X size={18}/></button></div><nav aria-label="Mobile navigation">{NAV_GROUPS.map(group=><div className="nav-group" key={group.label}><p>{group.label}</p>{group.keys.map(key=>{const item=NAV_ITEMS.find(nav=>nav.key===key);const Icon=item.icon;return <button className={`workspace-nav-item ${page===key ? "active" : ""}`} aria-current={page===key ? "page" : undefined} key={key} onClick={()=>{setPage(key);onClose();}}><Icon size={17}/><span>{item.label}</span></button>;})}</div>)}</nav><div className="mobile-nav-footer"><ScanSearch size={16}/>Evidence from your repository.</div></aside></>;
}

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
    node.x = 115;
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
      x: 115, y: 88, w: 190, h: 54,
      desc: "No known deployment or infrastructure architecture was detected from the repository files.",
    };
    ordered.push(application);
    edges.push({ from: "github", to: "application" });
  }

  return {
    nodes: ordered,
    edges,
    width: 420,
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

function ArchitectureDiagram({ full = false, onNodeClick, activeNode, zoom = 1 }) {
  const graph = buildArchitectureGraph();
  const W = graph.width;
  const H = graph.height;

  // Scale the fixed-size canvas down to the container so it never needs
  // sideways scrolling on phones/tablets.
  const wrapRef = useRef(null);
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return undefined;
    const update = () => setScale(Math.min(1, el.clientWidth / W) * zoom);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [W, zoom]);

  return (
    <div ref={wrapRef} className="w-full">
      <div className="relative mx-auto" style={{ width: W * scale, height: H * scale }}>
        <div
          className="absolute left-0 top-0"
          style={{ width: W, height: H, transform: `scale(${scale})`, transformOrigin: "top left" }}
        >
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="absolute inset-0">
            {graph.edges.map((edge, index) => {
              const a = graph.nodes.find((node) => node.id === edge.from);
              const b = graph.nodes.find((node) => node.id === edge.to);
              if (!a || !b) return null;
              const d = elbowPath(a, b);
              return (
                <g key={`${edge.from}-${edge.to}-${index}`}>
                  <path d={d} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
                  <path d={d} fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="4 5" opacity="0.4" />
                  <circle className="topology-particle" r="3" fill="#22d3ee">
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
                style={{
                  left: node.x,
                  top: node.y,
                  width: node.w,
                  height: node.h,
                  background: active ? "rgba(6,9,18,0.9)" : "rgba(11,17,32,0.9)",
                  border: active ? "1px solid rgba(34,211,238,0.4)" : "1px solid rgba(255,255,255,0.08)",
                }}
                className={`absolute flex items-center gap-2.5 rounded-lg px-3 text-left transition-all ${
                  active ? "ring-1 ring-cyan-400/40" : "hover:bg-white/[0.03]"
                } ${full ? "cursor-pointer" : "cursor-default"}`}
              >
                <div
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md"
                  style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)" }}
                >
                  <NodeIcon className="h-4 w-4 text-blue-400" strokeWidth={2} />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-slate-200">{node.label}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}


function GlassPanel({ eyebrow, title, icon: Icon, action, className = "", children }) {
  return (
    <section className={`glass-panel ${className}`}>
      <div className="glass-panel-heading">
        <div className="glass-panel-title">
          {Icon && <span className="panel-icon"><Icon size={17} /></span>}
          <div><span className="panel-eyebrow">{eyebrow}</span><h2>{title}</h2></div>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function RepositoryHealthGauge() {
  const score = Math.max(0, Math.min(100, Number(HEALTH.overall) || 0));
  const tone = scoreTone(score);
  const color = tone === "emerald" ? "#34d399" : tone === "amber" ? "#fbbf24" : "#fb7185";
  const circumference = 2 * Math.PI * 76;
  return (
    <div className="health-orbit" style={{ "--gauge-color": color }}>
      <svg viewBox="0 0 200 200" role="img" aria-label={HEALTH.overall===null ? "Repository health unavailable" : `Repository health: ${score} out of 100`}>
        <circle className="gauge-orbit" cx="100" cy="100" r="94" />
        <circle className="gauge-track" cx="100" cy="100" r="76" />
        <circle className="gauge-value" cx="100" cy="100" r="76"
          stroke={color} strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - score / 100)} transform="rotate(-90 100 100)" />
        <circle className="gauge-inner" cx="100" cy="100" r="62" />
        <text x="100" y="101" textAnchor="middle" className="gauge-score">{HEALTH.overall===null ? "—" : score}</text>
        <text x="100" y="122" textAnchor="middle" className="gauge-caption">OUT OF 100</text>
      </svg>
    </div>
  );
}

function OverviewPage({ setPage, onSelectIssue, onCloudResourcesClick, onAnalyze, analyzing }) {
  const [archActive, setArchActive] = useState(null);
  const [reducedMotion, setReducedMotion] = useState(() =>
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  const findings = ["critical", "high", "medium", "low"].map(name => ({ name, value: Number(SECURITY.findings?.[name] ?? 0) }));
  const total = findings.reduce((sum, item) => sum + item.value, 0);
  const priority = (SEVERITY_COUNTS.critical || 0) + (SEVERITY_COUNTS.high || 0);
  const rankedIssues = [...ISSUES].sort((a, b) =>
    ["critical", "high", "medium", "low"].indexOf(a.severity) - ["critical", "high", "medium", "low"].indexOf(b.severity));
  const workflows = ARCH.architectureLabels.filter(label => /CI.CD|Pipeline|DevOps|Actions/i.test(label));
  const selectedNode = buildArchitectureGraph().nodes.find(node => node.id === archActive);
  const go = (page, label) => <button className="glass-link" onClick={() => setPage(page)}>{label}<ArrowRight size={14} /></button>;

  return (
    <div className="neon-overview">
      <header className="intelligence-heading">
        <div><div className="page-kicker"><span /> REPOSITORY INTELLIGENCE</div>
          <h1>See the signal.<span> Ship with confidence.</span></h1>
          <p>Your code, security, and infrastructure. One intelligent perspective.</p>
        </div>
        <button className="neon-primary" onClick={onAnalyze} disabled={analyzing}>
          <RefreshCw size={15} className={analyzing ? "animate-spin" : ""} />
          {analyzing ? "Analyzing…" : "Run analysis"}
        </button>
      </header>

      <div className="repo-context-strip">
        <div className="repo-identity"><Github className="h-5 w-5" /><div><small>CONNECTED REPOSITORY</small><strong>{REPO.fullName}</strong></div></div>
        <span className="context-branch"><GitBranch size={13} />{REPO.branch}</span>
        {REPO.commitHash && <span className="context-commit"><GitCommit size={14} />{REPO.commitHash}</span>}
        <div className="context-analysis"><span className="status-dot" />Analysis complete<small>{REPO.lastAnalyzed}</small></div>
      </div>

      <section className="floating-metrics" aria-label="Repository metrics">
        {METRICS.map((metric, index) => {
          const Icon = metric.icon;
          return <button className={`floating-metric metric-${index}`} key={metric.label}
            onClick={() => metric.label === "Cloud Resources" ? onCloudResourcesClick() : setPage(metric.label === "Total Files" ? "repository" : metric.label === "Security Findings" ? "security" : "issues")}>
            <div className="metric-top"><span className="metric-icon"><Icon size={18} /></span><ArrowRight size={13} /></div>
            <strong>{metric.value}</strong><h2>{metric.label}</h2><p>{metric.note}</p>
            <div className="metric-light" aria-hidden="true" />
          </button>;
        })}
      </section>

      <div className="intelligence-grid">
        <GlassPanel className="health-glass" eyebrow="THE BIG PICTURE" title="Repository health" icon={ScanSearch} action={go("analysis", "Analysis")}>
          <div className="health-center"><RepositoryHealthGauge /><div className="health-verdict"><span className="glass-status">Latest assessment</span><h3>{HEALTH.status}</h3><p>Weighted scoring from your repository analysis.</p></div></div>
          <div className="health-score-list">{SUBSCORES.map(score => <div key={score.label}><span>{score.label}</span><ProgressBar value={score.value} tone={score.tone} /><strong>{score.value}<small>/100</small></strong></div>)}{!SUBSCORES.length && <p className="glass-muted">Score breakdown is unavailable for this analysis.</p>}</div>
        </GlassPanel>

        <GlassPanel className="security-glass" eyebrow="EXPOSURE & PRIORITY" title="Security intelligence" icon={ShieldAlert} action={go("security", "Full report")}>
          <div className="security-analytics">
            <div className="security-ring"><ResponsiveContainer width="100%" height={180}><PieChart><Pie isAnimationActive={!reducedMotion} data={total ? findings : [{name:"empty",value:1}]} dataKey="value" innerRadius={62} outerRadius={78} paddingAngle={total ? 5 : 0} cornerRadius={4} stroke="none" startAngle={90} endAngle={-270}>
              {(total ? findings : [{name:"empty"}]).map(item => <Cell key={item.name} fill={TONE[item.name]?.hex || "#23304b"} />)}
            </Pie><Tooltip contentStyle={{background:"#0b1429",border:"1px solid #33425a",borderRadius:10,color:"#e2e8f0"}} /></PieChart></ResponsiveContainer><div className="donut-label"><strong>{total}</strong><span>security findings</span></div></div>
            <div className="security-risk-summary"><span className="glass-muted">High-priority repository issues</span><strong>{priority}<span> to review</span></strong><p>Critical and high-severity findings across the repository.</p><div className="severity-bars">{findings.map(item => <div key={item.name}><i style={{background:TONE[item.name].hex}} /><span>{item.name}</span><strong>{item.value}</strong><div style={{"--severity-color":TONE[item.name].hex}}><span style={{width:`${total ? item.value / total * 100 : 0}%`}} /></div></div>)}</div></div>
          </div>
          <div className="security-findings"><div className="findings-subhead"><span>PRIORITY QUEUE</span>{go("issues", "View all findings")}</div>{rankedIssues.slice(0,3).map(issue => <button className="neon-finding" key={issue.id} onClick={() => onSelectIssue(issue)}><span className="finding-indicator" style={{background:TONE[issue.severity]?.hex}} /><div><strong>{issue.title}</strong><small>{issue.file} · {issue.category}</small></div><SeverityBadge severity={issue.severity} /><ChevronRight size={14} /></button>)}{!ISSUES.length && <div className="glass-empty"><CheckCircle2 size={19} />No issues detected in this repository analysis.</div>}</div>
        </GlassPanel>

        <GlassPanel className="topology-glass" eyebrow="EVIDENCE-BASED TOPOLOGY" title="Infrastructure architecture" icon={Cloud} action={go("architecture", "Explore map")}>
          <div className="topology-toolbar"><span className="topology-badge"><span className="status-dot" />Repository evidence</span><button onClick={onCloudResourcesClick}>{ARCH.services.length} cloud resources <ExternalLink size={12} /></button></div>
          <div className="neon-topology"><ArchitectureDiagram activeNode={archActive} onNodeClick={setArchActive} /></div>
          <div className="topology-insight" aria-live="polite"><span className="panel-icon">{selectedNode ? <Layers size={16} /> : <ScanSearch size={16} />}</span><div><strong>{selectedNode ? selectedNode.label : ARCH.provider}</strong><p>{selectedNode ? selectedNode.desc : ARCH.assessment}</p></div></div>
        </GlassPanel>

        <GlassPanel className="pipeline-glass" eyebrow="BUILD → SHIP → OBSERVE" title="Delivery pipeline" icon={Workflow} action={go("cicd", "Details")}>
          <div className="pipeline-status"><span className="glass-status">{workflows.length ? "Configuration detected" : "Awaiting configuration"}</span><small>Repository scan</small></div>
          <ol className="pipeline-flow">
            <li className="evidence-found"><span><Github className="h-4 w-4" /></span><div><strong>Source repository</strong><small>{REPO.name}</small></div><Check size={14} /></li>
            <li className={workflows.length ? "evidence-found" : ""}><span><Workflow size={16} /></span><div><strong>Workflow configuration</strong><small>{workflows.length ? workflows.join(" · ") : "No CI/CD configuration detected"}</small></div>{workflows.length ? <Check size={14} /> : <Minus size={14} />}</li>
            <li><span><Container size={16} /></span><div><strong>Build & deployment runs</strong><small>Execution telemetry unavailable</small></div><Circle size={12} /></li>
          </ol>
          <div className="pipeline-empty"><Plug size={18} /><div><strong>Run telemetry is not connected</strong><p>Stage results and execution history will appear when available. Configuration evidence is shown above.</p></div></div>
        </GlassPanel>

        <GlassPanel className="recommendations-glass" eyebrow="YOUR NEXT BEST ACTION" title="Priority recommendations" icon={Lightbulb} action={go("recommendations", "View all")}>
          <div className="neon-recommendations">{RECOMMENDATIONS.slice(0,3).map((rec,index) => <article key={rec.id}><span className="recommendation-number">{String(index + 1).padStart(2,"0")}</span><div><div><h3>{rec.title}</h3><SeverityBadge severity={rec.severity} /></div><p>{rec.action}</p>{rec.relatedIssue && ISSUES.some(issue => issue.id === rec.relatedIssue) && <button className="glass-link" onClick={() => onSelectIssue(ISSUES.find(issue => issue.id === rec.relatedIssue))}>Review issue <ArrowRight size={13} /></button>}</div></article>)}{!RECOMMENDATIONS.length && <div className="glass-empty"><CheckCircle2 size={20} />No recommendations from the latest analysis.</div>}</div>
        </GlassPanel>

        <GlassPanel className="activity-glass" eyebrow="LATEST SIGNALS" title="Analysis activity" icon={Clock}>
          <div className="neon-timeline">{ACTIVITY.map((activity,index) => <div key={`${activity.label}-${index}`}><span><Check size={12} /></span><div><strong>{activity.label}</strong><small>{activity.time}</small></div><span className="activity-done">Complete</span></div>)}</div>
          <div className="security-notice"><ShieldAlert size={17} /><div><strong>{priority ? `${priority} priority issues need your attention` : "No critical or high-priority issues"}</strong><p>From the latest repository analysis.</p></div><button aria-label="Review security findings" onClick={() => setPage("issues")}><ArrowRight size={16} /></button></div>
        </GlassPanel>
      </div>
      <div className="platform-split"><FutureAI/><FutureAI kind="prediction" onOpen={()=>setPage("intelligence")}/></div>
      <footer className="neon-footer"><Layers size={14} /><span>Cloud-ByteXL</span><i />Repository intelligence, illuminated.<span className="footer-source">Powered by your repository. Grounded in evidence.</span></footer>
    </div>
  );
}

function PageHeader({ eyebrow, title, description, action }) {
  return <header className="platform-heading"><div><div className="page-kicker"><span />{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}<span className="page-revision"><GitBranch size={12}/>{REPO.branch}<i/>{REPO.commitHash || "Revision unavailable"}</span></header>;
}

function PageStats({ items }) {
  return <div className="page-stats">{items.map(([label,value,Icon=Layers]) => <div key={label}><span className="panel-icon"><Icon size={18}/></span><div><small>{label}</small><strong>{value}</strong></div></div>)}</div>;
}

function EmptyPanel({ title, detail, icon: Icon = ScanSearch }) {
  return <div className="platform-empty"><span><Icon size={26}/></span><h3>{title}</h3><p>{detail}</p></div>;
}

function FindingRows({ items, onSelectIssue }) {
  return <div className="platform-findings">{items.length ? items.map(issue => <button key={issue.id} onClick={() => onSelectIssue(issue)}><SeverityBadge severity={issue.severity}/><div><strong>{issue.title}</strong><small>{issue.file}:{issue.line} · {issue.category}</small><p>{issue.why}</p></div><ChevronRight size={16}/></button>) : <EmptyPanel title="No matching findings" detail="No findings match the current repository analysis and filters." icon={CheckCircle2}/>}</div>;
}

function FileTreeNode({ node, onSelect, selected, depth=0 }) {
  const [expanded,setExpanded] = useState(depth === 0);
  const folder = Boolean(node.children);
  return <div><button className={`file-tree-item ${selected === node.path ? "selected" : ""}`} style={{paddingLeft:12+depth*14}} onClick={() => folder ? setExpanded(!expanded) : onSelect(node.path)} aria-expanded={folder ? expanded : undefined}>{folder ? <ChevronRight size={12} className={expanded ? "rotate-90" : ""}/> : <FileCode2 size={13}/>}<span>{node.name}</span>{folder && <small>{Object.keys(node.children).length}</small>}</button>{folder && expanded && Object.values(node.children).map(child => <FileTreeNode key={child.path} node={child} onSelect={onSelect} selected={selected} depth={depth+1}/>)}</div>;
}

function CodeExplorer({ paths, title="Source explorer" }) {
  const [selected,setSelected] = useState("");
  const [requestId,setRequestId] = useState(0);
  const [source,setSource] = useState({loading:false,text:"",error:""});
  const [query,setQuery] = useState("");
  const tree = {};
  paths.filter(path => path.toLowerCase().includes(query.toLowerCase())).forEach(path => {
    let level=tree;
    path.split("/").forEach((name,index,parts) => {
      if(!level[name]) level[name]={name,path:parts.slice(0,index+1).join("/"),...(index<parts.length-1 ? {children:{}} : {})};
      level=level[name].children;
    });
  });
  useEffect(() => {
    if(!selected) return;
    const controller = new AbortController();
    fetch(`${API_BASE}/api/github/file`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:REPO.url,path:selected,branch:REPO.analysisCommitSha || REPO.branch}),signal:controller.signal})
      .then(async response => {const data=await response.json();if(!response.ok || data.status!=="SUCCESS") throw new Error(data.message || "File preview is unavailable.");return data;})
      .then(data => setSource({loading:false,text:typeof data.content === "string" ? data.content : "",error:""}))
      .catch(error => {if(error.name!=="AbortError") setSource({loading:false,text:"",error:error.message});});
    return () => controller.abort();
  },[selected,requestId]);
  const selectFile = path => {setSource({loading:true,text:"",error:""});setSelected(path);setRequestId(id=>id+1);};
  return <GlassPanel title={title} eyebrow="REPOSITORY FILES" icon={FolderTree} className="explorer-panel"><div className="code-explorer"><aside><label className="search-field"><ScanSearch size={14}/><input aria-label="Search repository files" placeholder="Find a file…" value={query} onChange={e=>setQuery(e.target.value)}/></label><div className="file-tree">{Object.values(tree).map(node=><FileTreeNode key={node.path} node={node} selected={selected} onSelect={selectFile}/>)}{!Object.keys(tree).length && <p className="inline-empty">No matching files.</p>}</div></aside><div className="source-pane"><div className="source-toolbar"><FileCode2 size={14}/><span>{selected || "Select a file to inspect"}</span>{selected && <a href={`${REPO.url}/blob/${encodeURIComponent(REPO.analysisCommitSha || REPO.branch)}/${selected.split('/').map(encodeURIComponent).join('/')}`} target="_blank" rel="noreferrer" aria-label="Open source on GitHub"><ExternalLink size={14}/></a>}</div>{source.loading ? <div className="platform-empty" role="status"><Loader2 className="animate-spin"/>Reading source from GitHub…</div> : source.error ? <EmptyPanel title="Preview unavailable" detail={source.error}/> : selected ? <pre className="source-code">{source.text || "This file is empty or has no text preview."}</pre> : <EmptyPanel title="Explore the source of truth" detail="Expand a folder and select a file. Code previews are loaded from the connected repository." icon={Code2}/>}</div></div></GlassPanel>;
}

function RepositoryPage() {
  const paths=REPOSITORY_FILES.map(file=>typeof file === "string" ? file : file.path).filter(Boolean);
  const colors=["#22d3ee","#a78bfa","#34d399","#fbbf24","#fb7185"];
  return <div className="platform-page"><PageHeader eyebrow="SOURCE INTELLIGENCE" title="Repository explorer" description="Every file, contribution, and commit. Connected to your source of truth." action={<a className="neon-primary" href={REPO.url} target="_blank" rel="noreferrer"><Github className="h-4 w-4"/>Open repository</a>}/><PageStats items={[["Repository files",paths.length,Files],["Detected languages",LANGUAGES.length,Code2],["Contributors returned",CONTRIBUTORS.length,User],["Recent commits returned",COMMITS.length,GitCommit]]}/><div className="platform-split"><GlassPanel title={REPO.fullName} eyebrow="REPOSITORY PROFILE" icon={GitBranch}><div className="repo-profile"><h3>{REPO.name}</h3><p>{REPO.lastCommitMsg}</p><span><GitBranch size={14}/>{REPO.branch}</span><span><GitCommit size={14}/>{REPO.commitHash}</span></div><div className="language-layout">{LANGUAGES.length ? <><div className="language-donut"><ResponsiveContainer width="100%" height={180}><PieChart><Pie data={LANGUAGES} dataKey="pct" nameKey="name" innerRadius={53} outerRadius={72} paddingAngle={3} isAnimationActive={false}>{LANGUAGES.map((l,i)=><Cell key={l.name} fill={colors[i%colors.length]}/>)}</Pie><Tooltip contentStyle={{background:"#101b30",border:"1px solid #334155"}}/></PieChart></ResponsiveContainer></div><div>{LANGUAGES.map((language,index)=><div className="language-row" key={language.name}><i style={{background:colors[index%colors.length]}}/><span>{language.name}</span><strong>{language.pct}%</strong></div>)}</div></> : <EmptyPanel title="No language breakdown" detail="GitHub did not return language statistics for this repository."/>}</div></GlassPanel><GlassPanel title="The people behind the code" eyebrow="CONTRIBUTORS" icon={User}><div className="contributor-grid">{CONTRIBUTORS.map(person=><div key={person.name}><span>{person.name.slice(0,2).toUpperCase()}</span><div><strong>{person.name}</strong><small>{person.commits} contributions</small></div></div>)}{!CONTRIBUTORS.length && <EmptyPanel title="No contributor data" detail="No contributors were returned by GitHub."/>}</div></GlassPanel></div><CodeExplorer paths={paths}/><GlassPanel title="Recent changes" eyebrow="COMMIT FEED" icon={GitCommit}><div className="commit-feed">{COMMITS.map(commit=><a href={commit.url || REPO.url} target="_blank" rel="noreferrer" key={commit.hash}><span><GitCommit size={16}/></span><div><strong>{commit.message}</strong><small>{commit.author} · {commit.time}</small></div><code>{commit.hash}</code><ExternalLink size={13}/></a>)}</div></GlassPanel></div>;
}

function AnalysisPage({ onAnalyze, analyzing, onSelectIssue }) {
  return <div className="platform-page"><PageHeader eyebrow="SCANNING CENTER" title="From source to signal." description="Run a real repository scan and inspect the evidence behind every score." action={<button className="neon-primary" onClick={onAnalyze} disabled={analyzing}><RefreshCw size={15} className={analyzing ? "animate-spin" : ""}/>{analyzing ? "Analyzing…" : "Start analysis"}</button>}/><div className="platform-split analysis-layout"><GlassPanel title="Latest repository assessment" eyebrow="ANALYSIS RESULTS" icon={ScanSearch}><div className="analysis-score"><RepositoryHealthGauge/><div><span className="glass-status">{analyzing ? "Analysis in progress" : "Scan completed"}</span><h3>{HEALTH.status}</h3><p>{REPO.fullName}</p><small>{REPO.lastAnalyzed} · Duration {REPO.analysisDuration}</small></div></div><div className="health-score-list">{SUBSCORES.map(score=><div key={score.label}><span>{score.label}</span><ProgressBar value={score.value} tone={score.tone}/><strong>{score.value}/100</strong></div>)}</div></GlassPanel><GlassPanel title="Inspection coverage" eyebrow="SCAN SCOPE" icon={Layers}><div className="scan-scope">{["Repository files","Source configuration","Security rules","Architecture evidence","Recommendations"].map((label,index)=><div key={label}><span>{String(index+1).padStart(2,"0")}</span><strong>{label}</strong><small>Included in assessment</small></div>)}</div><div className="evidence-note">Progress reflects the request lifecycle. The backend does not stream individual scan stages.</div></GlassPanel></div><GlassPanel title="Recorded scans" eyebrow="ANALYSIS HISTORY" icon={Clock}><div className="scan-history">{ANALYSIS_HISTORY.map((scan,index)=><div key={index}><Clock size={16}/><span>{scan.date}</span><strong>{scan.score}/100</strong><small>{scan.issues} findings · {scan.duration}</small></div>)}</div></GlassPanel><GlassPanel title="Findings from this scan" eyebrow="INSPECTION RESULTS" icon={AlertTriangle}><FindingRows items={ISSUES.slice(0,5)} onSelectIssue={onSelectIssue}/></GlassPanel></div>;
}

function IssuesPage({ onSelectIssue }) {
  const [severity,setSeverity]=useState("all");const [query,setQuery]=useState("");const [category,setCategory]=useState("all");
  const filtered=ISSUES.filter(issue=>(severity==="all" || issue.severity===severity)&&(category==="all" || issue.category===category)&&`${issue.title} ${issue.file} ${issue.why}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="platform-page"><PageHeader eyebrow="FINDINGS WORKBENCH" title="Know what needs attention." description="Investigate configuration risks, understand their impact, and prioritize remediation."/><div className="severity-cards">{["critical","high","medium","low"].map(level=><button key={level} onClick={()=>setSeverity(severity===level ? "all" : level)} className={severity===level ? "selected" : ""} style={{"--severity-color":TONE[level].hex}}><SeverityBadge severity={level}/><strong>{SEVERITY_COUNTS[level] || 0}</strong><small>repository findings</small></button>)}</div><GlassPanel title="Finding inventory" eyebrow={`${filtered.length} MATCHING FINDINGS`} icon={AlertTriangle} action={<button className="glass-link" onClick={()=>{setQuery("");setSeverity("all");setCategory("all");}}>Reset filters <RefreshCw size={12}/></button>}><div className="filter-toolbar"><label className="search-field"><ScanSearch size={16}/><input aria-label="Search issues" placeholder="Search findings or affected files…" value={query} onChange={e=>setQuery(e.target.value)}/></label><select aria-label="Filter by category" value={category} onChange={e=>setCategory(e.target.value)}><option value="all">All categories</option>{[...new Set(ISSUES.map(issue=>issue.category))].map(value=><option key={value}>{value}</option>)}</select><select aria-label="Filter by severity" value={severity} onChange={e=>setSeverity(e.target.value)}>{["all","critical","high","medium","low"].map(value=><option key={value} value={value}>{value==="all" ? "All severities" : value}</option>)}</select></div>{filtered.length ? <div className="issue-table-wrap"><table className="issue-table"><thead><tr><th>Severity</th><th>Finding</th><th>Affected file</th><th>Category</th><th><span className="sr-only">Details</span></th></tr></thead><tbody>{filtered.map(issue=><tr key={issue.id}><td data-label="Severity"><SeverityBadge severity={issue.severity}/></td><td data-label="Finding"><button onClick={()=>onSelectIssue(issue)}>{issue.title}</button><p>{issue.why}</p></td><td data-label="File"><code>{issue.file}:{issue.line}</code></td><td data-label="Category">{issue.category}</td><td><button className="glass-link" onClick={()=>onSelectIssue(issue)} aria-label={`Inspect ${issue.title}`}>Inspect <ArrowRight size={13}/></button></td></tr>)}</tbody></table></div> : <EmptyPanel title="No matching findings" detail="Try a different search or severity filter."/>}</GlassPanel></div>;
}

function ArchitecturePage() {
  const [active,setActive]=useState(null);const [zoom,setZoom]=useState(1);const graph=buildArchitectureGraph();const node=graph.nodes.find(item=>item.id===active);
  return <div className="platform-page"><PageHeader eyebrow="INFRASTRUCTURE ATLAS" title="See how it connects." description={ARCH.reason}/><PageStats items={[["Detected components",graph.nodes.length,Layers],["Observed connections",graph.edges.length,Workflow],["Cloud resources",ARCH.services.length,Cloud],["Detection confidence",`${ARCH.confidence}%`,ScanSearch]]}/><div className="architecture-workbench"><GlassPanel title="Repository topology" eyebrow="INTERACTIVE ARCHITECTURE" icon={Cloud} action={<div className="zoom-controls"><button aria-label="Zoom out" onClick={()=>setZoom(Math.max(.5,zoom-.25))}><Minus size={15}/></button><span>{Math.round(zoom*100)}%</span><button aria-label="Zoom in" onClick={()=>setZoom(Math.min(2,zoom+.25))}><span>+</span></button><button onClick={()=>setZoom(1)}>Reset</button></div>}><div className="architecture-viewport"><ArchitectureDiagram full zoom={zoom} activeNode={active} onNodeClick={setActive}/></div><div className="evidence-note">Select a node to inspect its evidence. Connections represent repository configuration, not live cloud telemetry.</div></GlassPanel><div className="architecture-inspector"><GlassPanel title={node ? node.label : "Component inspector"} eyebrow="SELECTED COMPONENT" icon={Layers}>{node ? <div className="inspector-body"><span className="panel-icon"><node.icon size={20}/></span><p>{node.desc}</p><span className="glass-status">Repository evidence</span></div> : <EmptyPanel title="Select a component" detail="Choose a node in the topology to inspect its context."/>}</GlassPanel><GlassPanel title="Detection evidence" eyebrow={ARCH.provider} icon={FileCode2}><div className="evidence-chips">{ARCH.architectureLabels.map(label=><span key={label}>{label}</span>)}{!ARCH.architectureLabels.length && <p className="inline-empty">No recognized infrastructure configurations detected.</p>}</div><p className="inspector-assessment">{ARCH.assessment}</p></GlassPanel></div></div></div>;
}

function InfraFindingsPage({ title, category, onSelectIssue }) {
  const paths=REPOSITORY_FILES.map(file=>typeof file==="string" ? file : file.path).filter(Boolean);
  const items=ISSUES.filter(issue=>issue.category===category);
  const affected=new Set(items.map(issue=>issue.file));
  const files=paths.filter(path=>affected.has(path) || (category==="Docker" ? /(^|\/)(Dockerfile[^/]*|[^/]*\.dockerfile|docker-compose[^/]*|compose\.ya?ml|\.dockerignore)$/i.test(path) : /(^|\/)(k8s|kubernetes|helm|charts)(\/)|(^|\/)(deployment|service|ingress|statefulset|daemonset|configmap|secret|chart|values)\.ya?ml$/i.test(path)));
  return <div className="platform-page"><PageHeader eyebrow={category==="Docker" ? "CONTAINER INTELLIGENCE" : "ORCHESTRATION INTELLIGENCE"} title={`${title}, under the microscope.`} description={category==="Docker" ? "Inspect build configuration and container security from actual repository files." : "Review manifests, workload configuration, and YAML risks detected in your source."}/><PageStats items={[["Matching configuration files",files.length,FileCode2],["Related findings",items.length,AlertTriangle],["Priority findings",items.filter(issue=>["critical","high"].includes(issue.severity)).length,ShieldAlert],["Inspection source","Repository",GitBranch]]}/><div className="platform-split"><GlassPanel title="Configuration assessment" eyebrow="FINDINGS & REMEDIATION" icon={category==="Docker" ? Container : Boxes}><FindingRows items={items} onSelectIssue={onSelectIssue}/></GlassPanel><GlassPanel title="What this view knows" eyebrow="EVIDENCE BOUNDARY" icon={ScanSearch}><div className="inspector-body"><h3>{files.length ? "Configuration detected" : "No matching configuration detected"}</h3><p>{category==="Docker" ? "Dockerfiles and Compose configuration are identified from repository paths and analysis findings. Running images and container telemetry are unavailable." : "Matching manifests and Helm configuration are identified from repository paths and analysis findings. Cluster status and deployed workload counts are unavailable."}</p></div></GlassPanel></div><CodeExplorer paths={files} title={category==="Docker" ? "Dockerfile & Compose explorer" : "Manifest & YAML explorer"}/></div>;
}

function CICDPage({ onSelectIssue, onOpenIntelligence }) {
  const paths=REPOSITORY_FILES.map(file=>typeof file==="string" ? file : file.path).filter(Boolean).filter(path=>/(^|\/)\.github\/workflows\/|(^|\/)(Jenkinsfile|\.gitlab-ci\.ya?ml|azure-pipelines\.ya?ml)$/i.test(path));
  const findings=ISSUES.filter(issue=>issue.category==="CI/CD");
  return <div className="platform-page"><PageHeader eyebrow="DELIVERY OPERATIONS" title="From commit to deployment." description="Inspect pipeline configuration and delivery risks. Execution data is shown only when available."/><PageStats items={[["Workflow files",paths.length,Workflow],["Configuration findings",findings.length,AlertTriangle],["Latest execution","Unavailable",Clock],["Deployment status","Unavailable",Cloud]]}/><GlassPanel title="Delivery evidence" eyebrow="PIPELINE VISIBILITY" icon={Workflow}><div className="delivery-stages">{[["Source",REPO.name,true,GitBranch],["Workflow",paths.length ? `${paths.length} configurations detected` : "Not detected",paths.length>0,Workflow],["Execution","Run telemetry unavailable",false,Container],["Deployment","Deployment telemetry unavailable",false,Cloud]].map(([label,detail,available,Icon])=><div key={label} className={available ? "available" : ""}><span><Icon size={23}/></span><strong>{label}</strong><small>{detail}</small><em>{available ? "Evidence available" : "Not connected"}</em></div>)}</div></GlassPanel><div className="platform-split"><GlassPanel title="Execution history & logs" eyebrow="PERSISTED EXECUTIONS" icon={Clock}><button className="glass-link" onClick={onOpenIntelligence}>Open execution history <ArrowRight size={14}/></button><EmptyPanel title="Execution history is available in AI Intelligence" detail="Open AI Intelligence for persisted Actions attempts, historical evaluation and stored RCA. Syncing history is separate from source analysis; deployment telemetry is not inferred." icon={Plug}/></GlassPanel><FutureAI kind="prediction" onOpen={onOpenIntelligence}/></div><GlassPanel title="Pipeline configuration risks" eyebrow="FAILURE PREVENTION" icon={ShieldAlert}><FindingRows items={findings} onSelectIssue={onSelectIssue}/></GlassPanel><CodeExplorer paths={paths} title="Workflow source"/></div>;
}

function SecurityPage({ onSelectIssue }) {
  const values=["critical","high","medium","low"].map(name=>({name,value:Number(SECURITY.findings?.[name] || 0),fill:TONE[name].hex}));
  return <div className="platform-page"><PageHeader eyebrow="SECURITY OPERATIONS" title="Reduce exposure. Build trust." description="Security posture, severity distribution, and remediation priorities from the repository scan."/><PageStats items={[["Security score",SECURITY.score===null ? "Unavailable" : `${SECURITY.score}/100`,ShieldAlert],["Security findings",values.reduce((a,b)=>a+b.value,0),AlertTriangle],["Critical repository issues",SEVERITY_COUNTS.critical,AlertOctagon],["High repository issues",SEVERITY_COUNTS.high,AlertCircle]]}/><div className="platform-split"><GlassPanel title="Security posture" eyebrow="SEVERITY DISTRIBUTION" icon={ShieldAlert}><div className="security-posture"><div className="security-score-display"><strong>{SECURITY.score ?? "—"}</strong><small>SECURITY SCORE / 100</small><span className="glass-status">Latest repository scan</span></div><ResponsiveContainer width="100%" height={220}><BarChart data={values} layout="vertical" margin={{left:10,right:20}}><XAxis type="number" allowDecimals={false} stroke="#94a3b8" fontSize={10}/><YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} width={64}/><Tooltip contentStyle={{background:"#0b1429",border:"1px solid #334155"}}/><Bar dataKey="value" radius={[0,5,5,0]} isAnimationActive={false}>{values.map(item=><Cell key={item.name} fill={item.fill}/>)}</Bar></BarChart></ResponsiveContainer></div></GlassPanel><GlassPanel title="Remediation priorities" eyebrow="ACT ON THE EVIDENCE" icon={Lightbulb}><div className="remediation-summary">{["critical","high","medium","low"].map(level=><div key={level}><SeverityBadge severity={level}/><strong>{SEVERITY_COUNTS[level]}</strong><p>{level==="critical" ? "Review immediately" : level==="high" ? "Prioritize remediation" : level==="medium" ? "Schedule improvements" : "Review when practical"}</p></div>)}</div></GlassPanel></div><GlassPanel title="Priority repository alerts" eyebrow="CRITICAL & HIGH SEVERITY" icon={AlertOctagon}><FindingRows items={ISSUES.filter(issue=>["critical","high"].includes(issue.severity))} onSelectIssue={onSelectIssue}/></GlassPanel><GlassPanel title="All detected findings" eyebrow="INVESTIGATE & REMEDIATE" icon={ScanSearch}><FindingRows items={ISSUES} onSelectIssue={onSelectIssue}/></GlassPanel></div>;
}

function RecommendationsPage({ onSelectIssue }) {
  const [filter,setFilter]=useState("all");const list=RECOMMENDATIONS.filter(item=>filter==="all" || item.severity===filter);
  return <div className="platform-page"><PageHeader eyebrow="REMEDIATION STUDIO" title="Turn insight into action." description="Evidence-backed suggestions for your repository. Review and apply fixes in your own workflow."/><div className="platform-split"><PageStats items={[["Recommendations",RECOMMENDATIONS.length,Lightbulb],["Priority actions",RECOMMENDATIONS.filter(item=>["critical","high"].includes(item.severity)).length,ShieldAlert]]}/><div className="remediation-banner"><Lightbulb size={22}/><div><strong>Your changes stay in your hands.</strong><p>Suggestions are based on scan findings. No source changes are applied automatically.</p></div></div></div><div className="filter-toolbar"><span className="glass-muted">Filter recommendations</span><select aria-label="Filter recommendations" value={filter} onChange={e=>setFilter(e.target.value)}>{["all","critical","high","medium","low"].map(value=><option key={value} value={value}>{value==="all" ? "All severities" : value}</option>)}</select></div><div className="recommendation-board">{list.map((rec,index)=>{const issue=ISSUES.find(item=>item.id===rec.relatedIssue);return <GlassPanel key={rec.id} title={rec.title} eyebrow={`ACTION ${String(index+1).padStart(2,"0")}`} icon={Lightbulb} action={<SeverityBadge severity={rec.severity}/>}><div className="recommendation-body">{issue && <span className="affected-file"><FileCode2 size={13}/>{issue.file}:{issue.line}</span>}<h4>Why it matters</h4><p>{rec.why || issue?.why || "Review this recommendation against your repository configuration."}</p><h4>Suggested fix</h4><div className="suggested-fix">{rec.action}</div>{issue && <details><summary>Inspect detected configuration</summary><pre className="source-code">{issue.snippet}</pre></details>}{issue && <button className="glass-link" onClick={()=>onSelectIssue(issue)}>Open related finding <ArrowRight size={14}/></button>}</div></GlassPanel>;})}</div>{!list.length && <GlassPanel title="Recommendation queue" eyebrow="LATEST ASSESSMENT" icon={Lightbulb}><EmptyPanel title="No matching recommendations" detail="The current analysis has no recommendations at this severity." icon={CheckCircle2}/></GlassPanel>}</div>;
}

function FutureAI({ kind="chat", onOpen }) {
  if(kind==="prediction") return <GlassPanel title="Pipeline intelligence" eyebrow="AI INTELLIGENCE / EXPERIMENTAL" icon={Workflow}><div className="future-ai-body"><span className="planned-tag">Real Actions data · measured baselines</span><h3>Predict. Diagnose. Verify.</h3><p>Collect workflow history, evaluate an experimental model, and inspect evidence-grounded root causes. Readiness and limitations are reported from the backend.</p><button className="glass-link" onClick={onOpen}>Open AI Intelligence <ArrowRight size={14}/></button></div></GlassPanel>;
  return <GlassPanel title="AI DevOps copilot" eyebrow="PLANNED FEATURE · NOT ACTIVE" icon={Lightbulb} className="future-ai"><div className="future-ai-body"><span className="planned-tag">Coming in a future release</span><h3>Your next question. In context.</h3><p>A planned conversational workspace for repository findings and DevOps guidance. Chat is not connected.</p><div className="future-chat-input"><span>Ask about this repository…</span><button disabled aria-label="AI chat is not available"><ArrowRight size={16}/></button></div></div></GlassPanel>;
}

function ReportsPage({ onExport }) {
  const [preview,setPreview]=useState(true);
  return <div className="platform-page reports-page"><PageHeader eyebrow="INTELLIGENCE BRIEFING" title="The complete picture." description="An executive-ready view of repository health, security exposure, and recommended actions." action={<button className="neon-primary" onClick={onExport}><Download size={15}/>Download JSON report</button>}/><PageStats items={[["Health score",HEALTH.overall===null ? "Unavailable" : `${HEALTH.overall}/100`,ScanSearch],["Repository files",REPOSITORY_FILES.length,Files],["Findings",ISSUES.length,ShieldAlert],["Recommendations",RECOMMENDATIONS.length,Lightbulb]]}/><div className="report-controls"><span className="glass-status">Latest completed assessment</span><button className="glass-link" onClick={()=>setPreview(!preview)}>{preview ? "Hide report preview" : "Show report preview"}<FileBarChart2 size={14}/></button><button className="glass-link" onClick={()=>window.print()}>Print / save PDF <Download size={14}/></button></div>{preview && <div className="report-preview"><div className="report-cover"><span>CLOUD-BYTEXL / INTELLIGENCE REPORT</span><h2>{REPO.fullName}</h2><p>Repository assessment · {REPO.branch} · {REPO.commitHash}</p><strong>{HEALTH.status}</strong></div><GlassPanel title="Executive summary" eyebrow="01 / ASSESSMENT" icon={FileBarChart2}><div className="executive-summary"><RepositoryHealthGauge/><p>The latest analysis of <strong>{REPO.name}</strong> returned a health score of <strong>{HEALTH.overall}/100</strong>. Across {REPOSITORY_FILES.length} repository files, {ISSUES.length} findings were identified, including {SEVERITY_COUNTS.critical} critical and {SEVERITY_COUNTS.high} high-severity issues. {RECOMMENDATIONS.length} recommendations are available for review.</p></div></GlassPanel><div className="platform-split"><GlassPanel title="Health breakdown" eyebrow="02 / QUALITY" icon={ScanSearch}><div className="report-scores">{SUBSCORES.map(score=><div key={score.label}><span>{score.label}</span><ProgressBar value={score.value} tone={score.tone}/><strong>{score.value}/100</strong></div>)}</div></GlassPanel><GlassPanel title="Security exposure" eyebrow="03 / RISK" icon={ShieldAlert}><div className="report-security">{Object.entries(SECURITY.findings).map(([level,count])=><div key={level}><SeverityBadge severity={level}/><strong>{count}</strong></div>)}</div></GlassPanel></div><GlassPanel title="Recommended next steps" eyebrow="04 / ACTION PLAN" icon={Lightbulb}><div className="report-actions">{RECOMMENDATIONS.map((rec,index)=><div key={rec.id}><span>{index+1}</span><div><strong>{rec.title}</strong><p>{rec.action}</p></div><SeverityBadge severity={rec.severity}/></div>)}{!RECOMMENDATIONS.length && <p>No recommendations returned by this scan.</p>}</div></GlassPanel><div className="evidence-note">This report summarizes repository evidence. Runtime infrastructure status, live pipeline results, and AI predictions are not included.</div></div>}</div>;
}

/* ============================== MODALS & TOASTS ============================== */

function IssueDetailModal({ issue, onClose, onMarkReviewed, reviewed }) {
  if (!issue) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.72)", backdropFilter: "blur(8px)" }}
      onClick={onClose}
    >
      <div
        role="dialog" aria-modal="true" aria-label="Issue details"
        onKeyDown={event => {if(event.key === "Escape") onClose();}}
        className="w-full max-w-xl overflow-y-auto rounded-2xl shadow-2xl"
        style={{ maxHeight: "85vh", background: "#0b1120", border: "1px solid rgba(255,255,255,0.1)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="sticky top-0 flex items-start justify-between gap-4 p-5"
          style={{ background: "#0b1120", borderBottom: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div>
            <SeverityBadge severity={issue.severity} />
            <h3 className="mt-2 text-base font-bold text-slate-100">{issue.title}</h3>
            <div className="mt-1 font-mono text-xs text-faint">
              {issue.category} · {issue.file}:{issue.line}
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-1.5 text-muted transition-all hover:bg-white/[0.06] hover:text-slate-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 p-5">
          <div>
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              Detected Configuration
            </div>
            <pre
              className="overflow-x-auto rounded-xl p-4 font-mono text-xs text-slate-300"
              style={{ background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              {issue.snippet}
            </pre>
          </div>
          <div>
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              Why This Is a Problem
            </div>
            <p className="text-sm text-slate-300">{issue.why}</p>
          </div>
          <div>
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              Potential Impact
            </div>
            <p className="text-sm text-slate-300">{issue.impact}</p>
          </div>
          <div
            className="rounded-xl p-4"
            style={{ background: "rgba(59,130,246,0.07)", border: "1px solid rgba(59,130,246,0.2)" }}
          >
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-blue-400">
              Recommended Solution
            </div>
            <p className="text-sm text-slate-200">{issue.recommendation}</p>
          </div>
          <div>
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              Related Infrastructure
            </div>
            <p className="text-sm text-slate-300">{issue.related}</p>
          </div>
        </div>
        <div
          className="flex items-center justify-end gap-3 p-4"
          style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}
        >
          <button
            onClick={() => window.open(`${REPO.url}/blob/${encodeURIComponent(REPO.analysisCommitSha || REPO.branch)}/${issue.file.split('/').map(encodeURIComponent).join('/')}#L${issue.line || 1}`, "_blank", "noopener,noreferrer")}
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm text-slate-300 transition-all hover:text-slate-100"
            style={{ border: "1px solid rgba(255,255,255,0.09)" }}
          >
            <ExternalLink className="h-3.5 w-3.5" /> View on GitHub
          </button>
          <button
            onClick={() => onMarkReviewed(issue.id)}
            disabled={reviewed}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition-all hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Check className="h-3.5 w-3.5" />
            {reviewed ? "Reviewed" : "Mark as Reviewed"}
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.72)", backdropFilter: "blur(10px)" }}
      onClick={onClose}
    >
      <div
        role="dialog" aria-modal="true" aria-label="Connect GitHub repository"
        onKeyDown={event => {if(event.key === "Escape") onClose();}}
        className="w-full max-w-md rounded-2xl p-6 shadow-2xl"
        style={{ background: "#0b1120", border: "1px solid rgba(255,255,255,0.1)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-100">Connect GitHub Repository</h3>
            <p className="mt-0.5 text-sm text-muted">Enter any public repository URL to analyze</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-1.5 text-muted transition-all hover:bg-white/[0.06] hover:text-slate-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <label htmlFor="repository-url" className="mb-2 block text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
          Repository URL
        </label>
        <div
          className="mb-5 flex items-center gap-2.5 rounded-xl px-3 py-3 transition-all focus-within:ring-2 focus-within:ring-blue-500/30"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.09)" }}
        >
          <Github className="h-4 w-4 shrink-0 text-muted" />
          <input
            id="repository-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onConnect(url)}
            placeholder="github.com/your-org/your-repo"
            className="w-full bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none"
            autoFocus
          />
        </div>
        <button
          onClick={() => onConnect(url)}
          className="flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold text-white transition-all hover:bg-blue-500"
          style={{ background: "#2563eb", boxShadow: "0 0 18px rgba(59,130,246,0.35)" }}
        >
          <Plug className="h-4 w-4" />
          Connect &amp; Analyze Repository
        </button>
      </div>
    </div>
  );
}

function EmptyState({ onConnect }) {
  return (
    <div
      className="onboarding-view flex flex-col items-center justify-center px-6 text-center"
      style={{
        background: "radial-gradient(ellipse at 50% 30%, rgba(37,99,235,0.08) 0%, transparent 65%)",
      }}
    >
      <div
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl"
        style={{
          background: "linear-gradient(135deg, #1d4ed8 0%, #0891b2 100%)",
          boxShadow: "0 0 40px rgba(59,130,246,0.25)",
          border: "1px solid rgba(59,130,246,0.3)",
        }}
      >
        <Github className="h-9 w-9 text-white" />
      </div>

      <h1 className="text-2xl font-bold tracking-tight text-slate-100">
        Connect your GitHub repository
      </h1>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-muted">
        Let Cloud-ByteXL analyze your code, infrastructure, containers,
        Kubernetes configuration, and CI/CD pipeline — all in one place.
      </p>

      <button
        onClick={onConnect}
        className="mt-8 flex items-center gap-2.5 rounded-xl px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-blue-500"
        style={{ background: "#2563eb", boxShadow: "0 0 22px rgba(59,130,246,0.4)" }}
      >
        <Github className="h-4 w-4" />
        Connect Repository
      </button>

      <div className="mx-auto mt-12 grid w-full max-w-4xl grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: "Security Analysis", desc: "Detect vulnerabilities in Terraform, Docker, and Kubernetes configurations automatically." },
          { label: "CI/CD Intelligence", desc: "Inspect workflow configuration and delivery risks from repository evidence." },
          { label: "Architecture Mapping", desc: "Visualize your infrastructure stack from repository evidence, not assumptions." },
        ].map((f) => (
          <div
            key={f.label}
            className="rounded-xl p-4 text-left"
            style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}
          >
            <div className="mb-2 text-sm font-semibold text-slate-300">{f.label}</div>
            <div className="text-xs leading-relaxed text-faint">{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalyzingOverlay({ onCancel, elapsedSeconds }) {
  return <div className="scan-overlay" role="dialog" aria-modal="true" aria-label="Analyzing repository"><div className="scan-overlay-panel"><span className="scan-orb"><ScanSearch size={32}/></span><div className="page-kicker">REPOSITORY INTELLIGENCE</div><h2>Reading the signals.</h2><p role="status">Fetching repository metadata and reviewing bounded source evidence. Render Free may be waking up.</p><div className="scan-indeterminate" aria-label="Analysis in progress"><span/></div><div className="scan-overlay-scope">{ANALYSIS_STEPS.map(label=><span key={label}>{label}</span>)}</div><small>Elapsed: {elapsedSeconds}s. A scan timeout or error will return control to you.</small><button type="button" className="scan-cancel-button" onClick={onCancel} aria-label="Cancel repository analysis">Cancel scan and go back</button></div></div>;
}

function Toasts({ toasts }) {
  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-50 space-y-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="pointer-events-auto flex items-center gap-2.5 rounded-xl px-4 py-3 text-sm text-slate-100 shadow-2xl"
          style={{
            background: "rgba(14,21,37,0.95)",
            border: "1px solid rgba(255,255,255,0.1)",
            backdropFilter: "blur(12px)",
          }}
        >
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          {t.message}
        </div>
      ))}
    </div>
  );
}

function CloudResourcesModal({ resources, onClose }) {
  const resourceList = Array.isArray(resources) ? resources : [];
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(8px)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl overflow-hidden rounded-2xl shadow-2xl"
        style={{ background: "#0b1120", border: "1px solid rgba(255,255,255,0.1)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}
        >
          <div>
            <h2 className="text-lg font-bold text-white">Cloud Resources Found</h2>
            <p className="mt-1 text-sm text-muted">
              {resourceList.length} resources detected from the repository analysis
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-1.5 text-muted transition-all hover:bg-white/[0.06] hover:text-slate-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-6">
          {resourceList.length === 0 ? (
            <div
              className="rounded-xl p-8 text-center"
              style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              <Cloud className="mx-auto h-8 w-8 text-faint" />
              <p className="mt-3 text-sm font-medium text-slate-300">No cloud resources detected</p>
              <p className="mt-1 text-xs leading-5 text-faint">
                The repository analysis did not find provider-specific cloud resource definitions.
              </p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {resourceList.map((resource, index) => (
                <div
                  key={`${resource}-${index}`}
                  className="rounded-xl p-4"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className="mt-0.5 rounded-lg p-2"
                      style={{ background: "rgba(34,211,238,0.08)", border: "1px solid rgba(34,211,238,0.15)" }}
                    >
                      <Cloud className="h-4 w-4 text-cyan-400" />
                    </div>
                    <div className="min-w-0">
                      <div className="break-words text-sm font-medium text-slate-200">{resource}</div>
                      <div className="mt-1 text-xs text-faint">Detected resource</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div
          className="flex justify-end px-6 py-4"
          style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}
        >
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-200 transition-all hover:text-slate-100 hover:bg-white/[0.06]"
            style={{ border: "1px solid rgba(255,255,255,0.09)" }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

/* ============================== DATA FUNCTIONS ============================== */



/* ============================== APP ============================== */

export default function App() {
  const [collapsed, setCollapsed]           = useState(() => typeof window !== "undefined" && window.innerWidth < 1024);
  const [page, setPage]                     = useState("overview");
  const [viewMode, setViewMode] = useState("showcase");
  const [xray, setXray] = useState(false);
  const [mobileNavOpen, setMobileNavOpen]   = useState(false);
  const [repoConnected, setRepoConnected]   = useState(false);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showResourcesModal, setShowResourcesModal] = useState(false);
  const [connectionError,setConnectionError] = useState("");
  const analysisRequest = useRef(null);
  const [analyzing, setAnalyzing]           = useState(false);
  const [analysisElapsed, setAnalysisElapsed] = useState(0);
  const [analyzeStep, setAnalyzeStep]       = useState(0);
  const [selectedIssue, setSelectedIssue]   = useState(null);
  const [reviewedIds, setReviewedIds]       = useState([]);
  const [notifOpen, setNotifOpen]           = useState(false);
  const [profileOpen, setProfileOpen]       = useState(false);
  const [toasts, setToasts]                 = useState([]);
  useSyncExternalStore(subscribeRepository, getRepositoryRevision, getRepositoryRevision);
  useEffect(() => { window.scrollTo(0, 0); }, [page]);
  useEffect(() => () => analysisRequest.current?.abort(), []);
  useEffect(() => {
    if (!analyzing) return;
    const started = Date.now();
    const timer = setInterval(() => setAnalysisElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [analyzing]);
  useEffect(() => {
    if (!analyzing) return;
    const onEscape = (event) => {
      if (event.key === "Escape") {
        analysisRequest.current?.abort();
        analysisRequest.current = null;
        setAnalyzing(false);
        setConnectionError("Repository scan cancelled. You can retry or choose another repository.");
      }
    };
    window.addEventListener("keydown", onEscape);
    return () => window.removeEventListener("keydown", onEscape);
  }, [analyzing]);

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

    analysisRequest.current?.abort();
    const controller=new AbortController();analysisRequest.current=controller;
    setConnectionError("");
    setShowConnectModal(false);
    setAnalysisElapsed(0);
    setAnalyzing(true);
    setAnalyzeStep(1);
    pushToast("Connecting to GitHub…");

    try {
      const data = await requestJson(`${API_BASE}/api/github/repository`, {
        signal:controller.signal,timeoutMs:75000,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: repoUrl }),
      });

      if(controller.signal.aborted || analysisRequest.current!==controller)return;

      if (!data?.repository?.fullName || !data?.analysis || !Array.isArray(data?.files)) {
        throw new Error("Repository analysis returned incomplete evidence. Retry after checking Render availability.");
      }
      publishRepositoryData(data);
      setRepoConnected(true);
      if(data.databaseWarning)setConnectionError(data.databaseWarning);
      setAnalyzeStep(ANALYSIS_STEPS.length);
      setPage("overview");
      pushToast(`Connected to ${data.repository?.fullName || data.repository?.name}`);
    } catch (error) {
      if(error.name==="AbortError" || analysisRequest.current!==controller)return;
      setConnectionError(error.message || "Repository analysis unavailable.");
      // Preserve the last successfully analyzed repository when a refresh fails.
      pushToast(error.message || "Failed to connect GitHub repository");
    } finally {
      if(analysisRequest.current===controller){
        analysisRequest.current=null;
        setAnalyzing(false);
      }
    }
  };

  const handleMarkReviewed = (id) => {
    setReviewedIds((r) => [...r, id]);
    pushToast("Issue marked as reviewed");
  };

  const handleExport = () => {
    const report = {repository:REPO,health:HEALTH,subscores:SUBSCORES,security:SECURITY,issues:ISSUES,recommendations:RECOMMENDATIONS,architecture:ARCH};
    const url = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:"application/json"}));
    const anchor=document.createElement("a");anchor.href=url;anchor.download=`${REPO.name}-analysis.json`;anchor.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    pushToast("Repository analysis report downloaded");
  };

  const closeMenus = () => { setNotifOpen(false); setProfileOpen(false); };

  let content;
  // Historical AI evidence exists in Neon independently of a fresh, potentially
  // slow source scan. Do not gate the AI workspace behind repository analysis.
  if (page === "intelligence" && (!repoConnected || !REPO.url)) {
    content = <AIIntelligence repository="saksham-1326/Cloud-Byte-XL-Project" apiBase={API_BASE} />;
  } else if (!repoConnected || !REPO.url) {
    content = <EmptyState onConnect={() => setShowConnectModal(true)} />;
  } else {
    switch (page) {
      case "overview":
        content = <OverviewPage onAnalyze={runAnalysis} analyzing={analyzing} setPage={setPage} onSelectIssue={setSelectedIssue} onCloudResourcesClick={() => setShowResourcesModal(true)} />;
        break;
      case "repository":
        content = <RepositoryPage />;
        break;
      case "analysis":
        content = <AnalysisPage onAnalyze={runAnalysis} analyzing={analyzing} onSelectIssue={setSelectedIssue} />;
        break;
      case "issues":
        content = <IssuesPage onSelectIssue={setSelectedIssue} />;
        break;
      case "architecture":
        content = <ArchitecturePage />;
        break;
      case "docker":
        content = (
          <InfraFindingsPage
            title="Docker"
            subtitle="Container build and runtime configuration detected in the repository."
            category="Docker"
            onSelectIssue={setSelectedIssue}
          />
        );
        break;
      case "kubernetes":
        content = (
          <InfraFindingsPage
            title="Kubernetes"
            subtitle="Manifests, deployments, and services discovered in the cluster configuration."
            category="Kubernetes"
            onSelectIssue={setSelectedIssue}
          />
        );
        break;
      case "cicd":
        content = <CICDPage onSelectIssue={setSelectedIssue} onOpenIntelligence={()=>setPage("intelligence")} />;
        break;
      case "security":
        content = <SecurityPage onSelectIssue={setSelectedIssue} />;
        break;
      case "recommendations":
        content = <RecommendationsPage onSelectIssue={setSelectedIssue} />;
        break;
      case "intelligence":
        content = <AIIntelligence key={REPO.fullName} repository={REPO.fullName} apiBase={API_BASE} />;
        break;
      case "reports":
        content = <ReportsPage onExport={handleExport} />;
        break;
      default:
        content = <OverviewPage onAnalyze={runAnalysis} analyzing={analyzing} setPage={setPage} onSelectIssue={setSelectedIssue} onCloudResourcesClick={() => setShowResourcesModal(true)} />;
    }
  }

  const floatingDock = (
    <div className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2">
      <div className="flex items-center gap-1.5 rounded-full border border-slate-700/80 bg-[#0b1120]/90 p-1.5 shadow-2xl shadow-black/60 backdrop-blur-xl">
        <button
          type="button"
          onClick={() => { setViewMode("showcase"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
          className={`dock-btn inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-bold transition-all ${viewMode === "showcase" ? "active" : "text-slate-300 hover:text-white"}`}
        >
          <Compass className="h-3.5 w-3.5" />
          <span>Architecture</span>
        </button>
        <button
          type="button"
          onClick={() => { setViewMode("workspace"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
          className={`dock-btn inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-bold transition-all ${viewMode === "workspace" ? "active" : "text-slate-300 hover:text-white"}`}
        >
          <LayoutDashboard className="h-3.5 w-3.5" />
          <span>Workspace</span>
        </button>
        {viewMode === "showcase" && (
          <button
            type="button"
            onClick={() => setXray((v) => !v)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-bold transition-all ${xray ? "bg-cyan-400/20 text-cyan-200" : "text-cyan-300 hover:bg-slate-800"}`}
          >
            <ScanEye className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">X-Ray</span>
          </button>
        )}
        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors"
          aria-label="Scroll to top"
        >
          <ArrowUp className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );

  if (viewMode === "showcase") {
    return (
      <>
        <MissionControlLanding
          xray={xray}
          onToggleXray={() => setXray((v) => !v)}
          onOpenWorkspace={(targetPage) => {
            if (targetPage) setPage(targetPage);
            setViewMode("workspace");
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
        />
        {floatingDock}
      </>
    );
  }

  return (
    <div
      className={`app-frame min-h-screen text-slate-100 ${page === "overview" || !repoConnected ? "overview-frame" : ""}`}
      style={{ background: "var(--bg-base)" }}
      onClick={closeMenus}
    >
      <div className="ambient-scene" aria-hidden="true"><div className="ambient-wave wave-cyan" /><div className="ambient-wave wave-violet" /><div className="ambient-wave wave-emerald" /></div>
      {(
        <Sidebar
          repoConnected={repoConnected}
          collapsed={collapsed}
          setCollapsed={setCollapsed}
          page={page}
          setPage={setPage}
        />
      )}

      {(
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
          onMobileMenuOpen={() => setMobileNavOpen(true)}
        />
      )}

      {/* Mobile navigation drawer */}
      {(
        <MobileNav
          open={mobileNavOpen}
          onClose={() => setMobileNavOpen(false)}
          page={page}
          setPage={setPage}
        />
      )}

      <main
        className={`transition-all duration-300 ${
          collapsed ? "sm:pl-16" : "sm:pl-64"
        } pt-16`}
      >
        <div className="workspace-content mx-auto p-4 sm:p-6 lg:p-8">
          <div className="workspace-route" aria-label="Current workspace location">
            <div className="workspace-route__crumbs"><Layers size={14}/><span>Cloud-ByteXL</span><span className="route-divider">/</span><span>Engineering workspace</span><span className="route-divider">/</span><span>{NAV_ITEMS.find(item=>item.key===page)?.label || "Overview"}</span></div>
            <span className={`workspace-route__tag ${repoConnected ? "" : "workspace-route__tag--empty"}`}><i/>{repoConnected ? "REPOSITORY CONNECTED" : "AWAITING REPOSITORY"}</span>
          </div>
          {repoConnected && <div className="workspace-identity">
            <div className="workspace-identity__main"><span className="workspace-identity__icon">{page === "intelligence" ? <Sparkles size={21}/> : page === "security" ? <ShieldCheck size={21}/> : <Activity size={21}/>}</span><div><span className="workspace-identity__eyebrow">DEVOPS INTELLIGENCE / {NAV_GROUPS.find(group=>group.keys.includes(page))?.label.toUpperCase() || "WORKSPACE"}</span><h1>{NAV_ITEMS.find(item=>item.key===page)?.label || "Overview"} workspace</h1><p>Repository evidence, actionable findings and measured intelligence from your connected source.</p></div></div>
            <span className="workspace-identity__pill">EVIDENCE-FIRST · READ ONLY</span>
          </div>}
          {connectionError && <div className="ai-alert error" role="alert"><AlertTriangle size={18}/><p>{connectionError}</p></div>}
          {content}
        </div>
      </main>

      {/* Modals */}
      <ConnectRepoModal
        open={showConnectModal}
        onClose={() => setShowConnectModal(false)}
        onConnect={handleConnect}
      />
      {showResourcesModal && (
        <CloudResourcesModal
          resources={ARCH.services}
          onClose={() => setShowResourcesModal(false)}
        />
      )}
      <IssueDetailModal
        issue={selectedIssue}
        onClose={() => setSelectedIssue(null)}
        onMarkReviewed={handleMarkReviewed}
        reviewed={selectedIssue ? reviewedIds.includes(selectedIssue.id) : false}
      />
      {analyzing && <AnalyzingOverlay elapsedSeconds={analysisElapsed} onCancel={() => {
        analysisRequest.current?.abort();
        analysisRequest.current = null;
        setAnalyzing(false);
        setConnectionError("Repository scan cancelled. You can retry or choose another repository.");
      }} />}
      <Toasts toasts={toasts} />
      {floatingDock}
    </div>
  );
}
