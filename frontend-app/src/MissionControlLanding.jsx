import { useState } from "react";
import {
  Layers,
  ScanEye,
  ArrowUpRight,
  GitBranch,
  ShieldCheck,
  BrainCircuit,
  Database,
} from "lucide-react";

const NODES = {
  repo: {
    tag: "NODE 01 · INGESTION",
    title: "Incremental GitHub Actions Collector",
    file: "collector.py + github.py",
    desc: "Reads workflow runs, attempts, and exact commit SHAs so pre-queue ML features never leak future job outcomes.",
    pills: ["GET /actions/runs", "SHA Snapshots"],
    code: "run #142 | attempt 1 | sha a476582 | status: completed -> failure\ncaptured: 14 changed files, 2 workflow steps, failed job log stream",
  },
  guard: {
    tag: "NODE 02 · SECURITY",
    title: "Log Redaction & Frame Extraction",
    file: "observation.py + rca.py",
    desc: "Redacts configured secrets and common credential patterns before storing or sending evidence to any LLM provider.",
    pills: ["Secret Redaction", "Line Citations"],
    code: "redacted: 2 credential patterns (GITHUB_TOKEN, DATABASE_URL)\npreserved: line 189–190 exit frame -> ready for diagnosis",
  },
  ai: {
    tag: "NODE 03 · INTELLIGENCE",
    title: "Evidence-validated RCA + scikit-learn",
    file: "rca_facts.py + ml.py",
    desc: "Uses evidence-cited rule-based RCA in the hosted demo and compares experimental ML baselines without claiming reliable prospective accuracy.",
    pills: ["Optional Gemini provider", "prequeue-v2"],
    code: "RCA Guard: PASSED (0 unsupported claims)\nML Model: LogisticRegression (60/20/20 chronological split)",
  },
  db: {
    tag: "NODE 04 · PERSISTENCE",
    title: "Neon PostgreSQL 18",
    file: "store.py + ci_callbacks.py",
    desc: "Persists authenticated terminal CI callbacks, RCA reports, and manual human reviews with transactional idempotency.",
    pills: ["PostgreSQL 18", "CI-Tested"],
    code: "INSERT INTO ci_receipts (id, run_id, outcome) -> COMMIT OK\nverified across Flask restart in CI",
  },
};

const DNA_ITEMS = [
  {
    key: "react",
    code: "01 · UI",
    symbol: "Rc",
    sup: "19",
    accent: "text-cyan-400",
    label: "React + Vite 8",
    tag: "FRONTEND",
    title: "React 19 + Vite 8",
    body: "Powers the reactive single-page dashboard with external store subscriptions (repositoryData.js) and strict contract helpers (aiContract.js).",
  },
  {
    key: "flask",
    code: "02 · API",
    symbol: "Fl",
    sup: "3.1",
    accent: "text-emerald-400",
    label: "Python + Flask",
    tag: "BACKEND API",
    title: "Python 3.13 + Flask 3.1",
    body: "Handles repository analysis, HTTP 202 async AI task polling, and Bearer-authenticated durable CI callback endpoints.",
  },
  {
    key: "pg",
    code: "03 · DB",
    symbol: "Pg",
    sup: "18",
    accent: "text-blue-400",
    label: "PostgreSQL + psycopg",
    tag: "STORAGE",
    title: "PostgreSQL 18 + psycopg 3",
    body: "Persists workflow runs, model artifacts with SHA-256 checks, RCA reports, human reviews, and restart-safe CI receipts across 5 SQL migrations.",
  },
  {
    key: "gemini",
    code: "04 · RCA",
    symbol: "Gm",
    sup: "3.5",
    accent: "text-amber-400",
    label: "Evidence-based RCA",
    tag: "ROOT-CAUSE AI",
    title: "Optional Gemini provider",
    body: "The deployed demo uses bounded, redacted evidence rules; optional LLM RCA is not enabled on the public Free hosting.",
  },
  {
    key: "sklearn",
    code: "05 · ML",
    symbol: "Sk",
    sup: "ML",
    accent: "text-cyan-400",
    label: "scikit-learn",
    tag: "ML PREDICTION",
    title: "scikit-learn + NumPy + joblib",
    body: "Evaluates DummyClassifier, Logistic Regression, and Random Forest on chronological 60/20/20 splits using prequeue-v2 features.",
  },
  {
    key: "tailwind",
    code: "06 · CSS",
    symbol: "Tw",
    sup: "3",
    accent: "text-sky-400",
    label: "Tailwind + Recharts",
    tag: "UI & CHARTS",
    title: "Tailwind CSS 3 + Recharts",
    body: "Delivers responsive desktop, tablet, and mobile layouts with crisp data visualizations for health scores and workflow history.",
  },
  {
    key: "docker",
    code: "07 · OPS",
    symbol: "Dk",
    sup: "CI",
    accent: "text-blue-400",
    label: "Docker + Actions",
    tag: "CONTAINERS & CI",
    title: "Docker + GitHub Actions",
    body: "Verifies containerized Python 3.13 runtime builds and runs automated CI pipelines with PostgreSQL 18 service containers.",
  },
  {
    key: "pytest",
    code: "08 · QA",
    symbol: "Py",
    sup: "CI",
    accent: "text-emerald-400",
    label: "pytest Verified",
    tag: "VERIFICATION",
    title: "pytest (174 Passing Tests)",
    body: "Covers AI API storage, ML audit rules, RCA fact guards, PostgreSQL migrations, and durable callback persistence.",
  },
];

export default function MissionControlLanding({ onOpenWorkspace, xray, onToggleXray }) {
  const [activeNode, setActiveNode] = useState("repo");
  const [diffMode, setDiffMode] = useState("clarity");
  const [activeDna, setActiveDna] = useState("react");

  const node = NODES[activeNode];
  const dna = DNA_ITEMS.find((item) => item.key === activeDna) || DNA_ITEMS[0];

  return (
    <div className={`min-h-screen bg-[#070b14] text-slate-100 ${xray ? "xray-on" : ""}`}>
      {/* Slim Top Status Bar */}
      <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#070b14]/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 text-slate-950 font-extrabold shadow-lg shadow-cyan-500/20">
              <Layers className="h-4 w-4" />
            </div>
            <span className="font-display text-base font-bold tracking-tight text-white">Cloud-ByteXL</span>
            <span className="hidden sm:inline-block rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-emerald-300">
              ● 174 TESTS PASS
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onToggleXray}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 font-mono text-[11px] font-semibold transition-all ${
                xray
                  ? "border-cyan-400 bg-cyan-400/15 text-cyan-200"
                  : "border-slate-700 bg-slate-900/90 text-cyan-300 hover:border-cyan-400/60"
              }`}
            >
              <ScanEye className="h-3.5 w-3.5" />
              <span>X-Ray Stack</span>
            </button>
            <button
              type="button"
              onClick={() => onOpenWorkspace("overview")}
              className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-4 py-1.5 text-xs font-bold text-slate-950 shadow-lg shadow-cyan-500/25 hover:from-cyan-300 hover:to-blue-400 transition-all"
            >
              <span>Open Workspace</span>
              <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </header>

      <main className="blueprint-grid hero-mesh pb-28">
        {/* Centered Architectural Hero + Interactive 4-Node Pipeline */}
        <section className="mx-auto max-w-6xl px-4 pt-12 pb-12 text-center sm:px-6 sm:pt-16 lg:px-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3.5 py-1 font-mono text-[11px] font-semibold text-cyan-300">
            <span>AI-POWERED DEVOPS INTELLIGENCE</span>
            <span className="text-slate-500">|</span>
            <span>POSTGRESQL 17 · GEMINI RCA · SCIKIT-LEARN</span>
          </div>

          <h1 className="font-display mx-auto mt-5 max-w-4xl text-4xl font-bold tracking-tight text-white sm:text-6xl lg:leading-[1.06]">
            Every failed pipeline has a{" "}
            <span className="bg-gradient-to-r from-cyan-300 via-sky-400 to-emerald-300 bg-clip-text text-transparent">
              verifiable story
            </span>
            .
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-slate-300 sm:text-base">
            Click any node in the live architecture pipeline below to inspect how Cloud-ByteXL ingests GitHub Actions logs, redacts secrets, validates AI root-cause diagnoses, and persists durable receipts.
          </p>

          {/* 4-Node Pipeline Graph */}
          <div className="relative mx-auto mt-10 max-w-5xl">
            <svg
              className="pointer-events-none absolute left-0 top-1/2 hidden h-8 w-full -translate-y-1/2 md:block"
              viewBox="0 0 1000 32"
              fill="none"
              preserveAspectRatio="none"
            >
              <line x1="120" y1="16" x2="880" y2="16" stroke="rgba(56, 189, 248, 0.22)" strokeWidth="2" />
              <line x1="120" y1="16" x2="880" y2="16" stroke="#22d3ee" strokeWidth="2" className="flow-dash" />
            </svg>

            <div className="relative z-10 grid gap-4 md:grid-cols-4">
              {[
                { id: "repo", label: "GitHub Collector", sub: "Actions runs, jobs & SHA snapshots", num: "NODE 01", Icon: GitBranch, color: "bg-cyan-400/15 text-cyan-300 border-cyan-400/30" },
                { id: "guard", label: "Secret Redactor", sub: "Strips tokens & preserves line numbers", num: "NODE 02", Icon: ShieldCheck, color: "bg-amber-400/15 text-amber-300 border-amber-400/30" },
                { id: "ai", label: "Evidence RCA + ML", sub: "Fact-guarded diagnosis & risk score", num: "NODE 03", Icon: BrainCircuit, color: "bg-emerald-400/15 text-emerald-300 border-emerald-400/30" },
                { id: "db", label: "PostgreSQL 18", sub: "Durable CI receipts & human reviews", num: "NODE 04", Icon: Database, color: "bg-blue-400/15 text-blue-300 border-blue-400/30" },
              ].map(({ id, label, sub, num, Icon, color }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setActiveNode(id)}
                  className={`node-card mc-glass-panel rounded-2xl p-4 text-left ${activeNode === id ? "active" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`flex h-9 w-9 items-center justify-center rounded-xl border ${color}`}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className={`font-mono text-[10px] font-bold ${activeNode === id ? "text-cyan-300" : "text-slate-400"}`}>
                      {num}
                    </span>
                  </div>
                  <div className="mt-3 text-sm font-bold text-white">{label}</div>
                  <div className="mt-0.5 text-xs text-slate-400">{sub}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Live Morphing Node Inspector */}
          <div className="mc-glass-panel relative mx-auto mt-5 max-w-5xl rounded-2xl p-5 text-left shadow-2xl">
            <span className="xray-badge absolute right-4 top-4 rounded-full bg-cyan-400 px-2.5 py-0.5 font-mono text-[10px] font-bold text-slate-950">
              backend/ai_intelligence/
            </span>
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <span className="rounded-md border border-cyan-400/30 bg-cyan-400/15 px-2.5 py-1 font-mono text-[11px] font-bold text-cyan-300">
                  {node.tag}
                </span>
                <h3 className="text-sm font-bold text-white">{node.title}</h3>
              </div>
              <span className="font-mono text-xs text-slate-400">{node.file}</span>
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-12">
              <div className="lg:col-span-5">
                <p className="text-xs leading-relaxed text-slate-300">{node.desc}</p>
                <div className="mt-3 flex flex-wrap gap-1.5 font-mono text-[11px]">
                  {node.pills.map((pill) => (
                    <span key={pill} className="rounded-full bg-slate-800 px-2.5 py-0.5 text-cyan-300">
                      {pill}
                    </span>
                  ))}
                </div>
              </div>
              <div className="lg:col-span-7">
                <pre className="overflow-x-auto rounded-xl border border-slate-800 bg-[#050810] p-3.5 font-mono text-xs leading-relaxed text-slate-200">
                  {node.code}
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* High-Contrast Ivory Section: Chaos vs Clarity Diff */}
        <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="ivory-panel relative rounded-3xl p-6 sm:p-8">
            <span className="xray-badge absolute right-6 top-6 rounded-full bg-slate-900 px-2.5 py-0.5 font-mono text-[10px] font-bold text-cyan-300">
              React 19 + Tailwind 3
            </span>
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div>
                <span className="font-mono text-xs font-bold uppercase tracking-widest text-sky-700">
                  Why Cloud-ByteXL Exists
                </span>
                <h2 className="font-display mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
                  From Raw Log Noise to Grounded Proof
                </h2>
              </div>
              <div className="inline-flex rounded-full bg-slate-200/80 p-1 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setDiffMode("chaos")}
                  className={`rounded-full px-4 py-1.5 transition-all ${
                    diffMode === "chaos" ? "bg-slate-950 text-white shadow" : "text-slate-700 hover:text-slate-950"
                  }`}
                >
                  Without Cloud-ByteXL
                </button>
                <button
                  type="button"
                  onClick={() => setDiffMode("clarity")}
                  className={`rounded-full px-4 py-1.5 transition-all ${
                    diffMode === "clarity" ? "bg-slate-950 text-white shadow" : "text-slate-700 hover:text-slate-950"
                  }`}
                >
                  With Cloud-ByteXL
                </button>
              </div>
            </div>

            {diffMode === "chaos" ? (
              <div className="mt-6 rounded-2xl bg-[#090e1a] p-5 text-slate-300">
                <div className="mb-2 font-mono text-[11px] text-rose-400">RAW UNSTRUCTURED LOG WALL (1,240 LINES)</div>
                <pre className="overflow-x-auto font-mono text-[11px] leading-relaxed">
{`2026-11-20T14:10:01Z [info] Setup Python 3.13...
2026-11-20T14:10:44Z [warn] Deprecated cache key...
2026-11-20T14:11:12Z [err] Connection refused
2026-11-20T14:11:13Z [err] Cleanup container failed (masking primary error)
2026-11-20T14:11:14Z Process completed with exit code 1.`}
                </pre>
              </div>
            ) : (
              <div className="mt-6 grid gap-4 lg:grid-cols-12">
                <div className="rounded-2xl bg-[#090e1a] p-5 text-slate-200 lg:col-span-7">
                  <div className="mb-2 flex items-center justify-between font-mono text-[11px] text-slate-400">
                    <span>EVIDENCE-CITED DIAGNOSIS</span>
                    <span className="rounded bg-emerald-500/20 px-2 py-0.5 font-bold text-emerald-300">GUARD PASSED</span>
                  </div>
                  <h3 className="text-base font-bold text-white">PostgreSQL service unavailable during durable callback test</h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-slate-300">
                    Integration test failed at <code className="text-cyan-300">line 189–190</code> because port 5432 refused connection before container readiness.
                  </p>
                  <pre className="mt-3 overflow-x-auto rounded-xl bg-[#050810] p-3 font-mono text-[11px] text-slate-300">
                    line 189 | <span className="mc-log-highlight">FAILED</span> tests/test_ci_durable.py::test_callback_idempotency
                    {"\n"}line 190 | psycopg.OperationalError: localhost:5432 refused
                  </pre>
                </div>
                <div className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 lg:col-span-5">
                  <div>
                    <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-sky-700">Recommended Fix</span>
                    <p className="mt-2 text-sm font-semibold text-slate-900">Start PostgreSQL 18 healthcheck before running pytest.</p>
                    <p className="mt-1 text-xs text-slate-600">Secondary cleanup errors are separated so they never mask the real root cause.</p>
                  </div>
                  <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 font-mono text-[11px]">
                    <span className="text-slate-500">Example: evidence rules (illustrative)</span>
                    <span className="font-bold text-emerald-700">0 Invented Quotes</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Tech Stack DNA Periodic Matrix */}
        <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <span className="font-mono text-xs font-bold uppercase tracking-widest text-cyan-400">Under the Hood · Tech DNA</span>
              <h2 className="font-display mt-1 text-2xl font-bold text-white sm:text-3xl">What Built This Platform</h2>
            </div>
            <p className="text-xs text-slate-400">Click any element tile to inspect its exact role in Cloud-ByteXL.</p>
          </div>

          <div className="grid gap-6 lg:grid-cols-12">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:col-span-7">
              {DNA_ITEMS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setActiveDna(item.key)}
                  className={`dna-tile mc-glass-panel rounded-2xl p-4 text-left ${activeDna === item.key ? "active" : ""}`}
                >
                  <div className={`font-mono text-[10px] ${item.accent}`}>{item.code}</div>
                  <div className="font-display mt-1 text-2xl font-bold text-white">
                    {item.symbol}
                    <span className={`text-sm ${item.accent}`}>{item.sup}</span>
                  </div>
                  <div className="mt-1 text-xs font-semibold text-slate-300">{item.label}</div>
                </button>
              ))}
            </div>

            <div className="mc-glass-panel flex flex-col justify-between rounded-2xl p-6 lg:col-span-5">
              <div>
                <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-cyan-400">{dna.tag}</span>
                <h3 className="font-display mt-1 text-2xl font-bold text-white">{dna.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-300">{dna.body}</p>
              </div>
              <div className="mt-5 flex items-center justify-between border-t border-slate-800 pt-4">
                <span className="font-mono text-[11px] text-slate-400">Want to see it in action?</span>
                <button
                  type="button"
                  onClick={() => onOpenWorkspace("intelligence")}
                  className="rounded-full bg-cyan-400 px-4 py-1.5 text-xs font-bold text-slate-950 hover:bg-cyan-300 transition-colors"
                >
                  Open AI Intelligence →
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
