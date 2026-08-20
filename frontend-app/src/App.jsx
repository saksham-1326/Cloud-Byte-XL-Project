import { useEffect, useState } from "react";

const BACKEND_URL = "http://127.0.0.1:5000";

function App() {
  const [message, setMessage] = useState("");

  const [githubData, setGithubData] = useState(null);
  const [ciData, setCiData] = useState(null);
  const [databaseStats, setDatabaseStats] = useState(null);
  const [deployments, setDeployments] = useState([]);
  const [failures, setFailures] = useState([]);

  const [loading, setLoading] = useState(false);
  const [backendLoading, setBackendLoading] = useState(false);

  // ============================================================
  // Generic API helper
  // ============================================================

  const fetchAPI = async (endpoint) => {
    const response = await fetch(`${BACKEND_URL}${endpoint}`);

    if (!response.ok) {
      throw new Error(`API request failed: ${endpoint}`);
    }

    return response.json();
  };

  // ============================================================
  // Load complete dashboard
  // ============================================================

  const loadDashboard = async () => {
    setLoading(true);
    setMessage("");

    try {
      const [
        github,
        ci,
        database,
        deploymentData,
        failureData,
      ] = await Promise.all([
        fetchAPI("/api/github/latest"),
        fetchAPI("/api/ci/status"),
        fetchAPI("/api/database/stats"),
        fetchAPI("/api/deployments"),
        fetchAPI("/api/failures"),
      ]);

      setGithubData(github);
      setCiData(ci);
      setDatabaseStats(database);
      setDeployments(deploymentData.deployments || []);
      setFailures(failureData.failures || []);

      setMessage("Dashboard updated successfully.");
    } catch (error) {
      console.error("Dashboard error:", error);

      setMessage(
        "Could not load dashboard data. Make sure Flask is running on port 5000."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Test backend
  // ============================================================

  const testBackend = async () => {
    setBackendLoading(true);
    setMessage("");

    try {
      const data = await fetchAPI("/");

      setMessage(data.message || "Backend connection successful.");
    } catch (error) {
      console.error("Backend error:", error);

      setMessage(
        "Could not connect to Flask backend."
      );
    } finally {
      setBackendLoading(false);
    }
  };

  // ============================================================
  // Load dashboard on startup
  // ============================================================

  useEffect(() => {
    loadDashboard();
  }, []);

  // ============================================================
  // Status helpers
  // ============================================================

  const getStatusColor = (status) => {
    const value = String(status || "").toUpperCase();

    if (value === "SUCCESS" || value === "PASSED") {
      return "#16a34a";
    }

    if (
      value === "FAILURE" ||
      value === "FAILED"
    ) {
      return "#dc2626";
    }

    if (value === "RECEIVED") {
      return "#d97706";
    }

    return "#64748b";
  };

  const getStatusBackground = (status) => {
    const value = String(status || "").toUpperCase();

    if (value === "SUCCESS" || value === "PASSED") {
      return "#dcfce7";
    }

    if (
      value === "FAILURE" ||
      value === "FAILED"
    ) {
      return "#fee2e2";
    }

    if (value === "RECEIVED") {
      return "#fef3c7";
    }

    return "#f1f5f9";
  };

  // ============================================================
  // Latest commit
  // ============================================================

  const latestCommit =
    githubData?.commits &&
    githubData.commits.length > 0
      ? githubData.commits[0]
      : null;

  // ============================================================
  // Main UI
  // ============================================================

  return (
    <div style={styles.page}>

      {/* ======================================================
          FLOATING BACKGROUND
      ====================================================== */}

      <div style={styles.backgroundOrbOne}></div>
      <div style={styles.backgroundOrbTwo}></div>

      <div style={styles.container}>

        {/* ====================================================
            HEADER
        ==================================================== */}

        <header style={styles.header}>

          <div>
            <div style={styles.logoRow}>
              <div style={styles.logo}>
                CB
              </div>

              <div>
                <h1 style={styles.title}>
                  Cloud-ByteXL
                </h1>

                <p style={styles.subtitle}>
                  DevOps CI/CD Monitoring Dashboard
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={loadDashboard}
            disabled={loading}
            style={{
              ...styles.primaryButton,
              opacity: loading ? 0.7 : 1,
              cursor: loading
                ? "not-allowed"
                : "pointer",
            }}
          >
            <span style={styles.buttonIcon}>
              ↻
            </span>

            {loading
              ? "Refreshing..."
              : "Refresh Dashboard"}
          </button>

        </header>

        {/* ====================================================
            MESSAGE
        ==================================================== */}

        {message && (
          <div style={styles.messageBox}>
            <span style={styles.messageDot}></span>

            <span>{message}</span>
          </div>
        )}

        {/* ====================================================
            TOP STATUS CARDS
        ==================================================== */}

        <section>

          <div style={styles.sectionHeading}>
            <div>
              <h2 style={styles.sectionTitle}>
                Pipeline Overview
              </h2>

              <p style={styles.sectionSubtitle}>
                Current CI/CD pipeline health
              </p>
            </div>

            <StatusBadge
              status={
                ciData?.status || "UNKNOWN"
              }
              getStatusColor={getStatusColor}
              getStatusBackground={
                getStatusBackground
              }
            />
          </div>

          <div style={styles.statusGrid}>

            <StatusCard
              title="Overall Status"
              value={
                ciData?.status || "UNKNOWN"
              }
              icon="●"
              color={getStatusColor(
                ciData?.status
              )}
              background={getStatusBackground(
                ciData?.status
              )}
            />

            <StatusCard
              title="Build"
              value={
                ciData?.build || "UNKNOWN"
              }
              icon="⚙"
              color={getStatusColor(
                ciData?.build
              )}
              background={getStatusBackground(
                ciData?.build
              )}
            />

            <StatusCard
              title="Tests"
              value={
                ciData?.tests || "UNKNOWN"
              }
              icon="✓"
              color={getStatusColor(
                ciData?.tests
              )}
              background={getStatusBackground(
                ciData?.tests
              )}
            />

            <StatusCard
              title="Docker"
              value={
                ciData?.docker || "UNKNOWN"
              }
              icon="◆"
              color={getStatusColor(
                ciData?.docker
              )}
              background={getStatusBackground(
                ciData?.docker
              )}
            />

          </div>

          <div style={styles.workflowCard}>
            <div style={styles.workflowIcon}>
              ⚡
            </div>

            <div>
              <div style={styles.smallLabel}>
                ACTIVE WORKFLOW
              </div>

              <div style={styles.workflowName}>
                {ciData?.workflow ||
                  "Cloud-ByteXL CI"}
              </div>
            </div>

            <div style={styles.workflowLine}></div>

            <div style={styles.workflowStatus}>
              ● Pipeline Connected
            </div>
          </div>

        </section>

        {/* ====================================================
            GITHUB + DATABASE
        ==================================================== */}

        <div style={styles.twoColumnGrid}>

          {/* ==================================================
              GITHUB
          ================================================== */}

          <section style={styles.panel}>

            <div style={styles.panelHeader}>
              <div>
                <h2 style={styles.panelTitle}>
                  GitHub Activity
                </h2>

                <p style={styles.panelSubtitle}>
                  Latest repository activity
                </p>
              </div>

              <div style={styles.githubIcon}>
                GH
              </div>
            </div>

            {githubData ? (
              <>

                <div style={styles.infoGrid}>

                  <InfoCard
                    title="Repository"
                    value={
                      githubData.repository ||
                      "Unknown"
                    }
                  />

                  <InfoCard
                    title="Branch"
                    value={
                      githubData.branch ||
                      "Unknown"
                    }
                  />

                  <InfoCard
                    title="Event"
                    value={
                      githubData.event ||
                      "Unknown"
                    }
                  />

                  <InfoCard
                    title="Pusher"
                    value={
                      githubData.pusher ||
                      "Unknown"
                    }
                  />

                </div>

                <div style={styles.commitCard}>

                  <div style={styles.commitHeader}>
                    <h3 style={styles.commitTitle}>
                      Latest Commit
                    </h3>

                    <span style={styles.commitBadge}>
                      COMMIT
                    </span>
                  </div>

                  {latestCommit ? (
                    <>

                      <p style={styles.commitMessage}>
                        {latestCommit.message ||
                          "No commit message"}
                      </p>

                      <div style={styles.commitDetails}>

                        <div>
                          <span style={styles.detailLabel}>
                            Commit ID
                          </span>

                          <span style={styles.commitId}>
                            {latestCommit.id
                              ? latestCommit.id.slice(
                                  0,
                                  12
                                )
                              : "Unknown"}
                          </span>
                        </div>

                        <div>
                          <span style={styles.detailLabel}>
                            Author
                          </span>

                          <span style={styles.detailValue}>
                            {latestCommit.author
                              ?.name ||
                              "Unknown"}
                          </span>
                        </div>

                      </div>

                    </>
                  ) : (
                    <p style={styles.emptyText}>
                      No commit information available.
                    </p>
                  )}

                </div>

              </>
            ) : (
              <LoadingText text="Loading GitHub information..." />
            )}

          </section>

          {/* ==================================================
              DATABASE
          ================================================== */}

          <section style={styles.panel}>

            <div style={styles.panelHeader}>
              <div>
                <h2 style={styles.panelTitle}>
                  Database
                </h2>

                <p style={styles.panelSubtitle}>
                  PostgreSQL system statistics
                </p>
              </div>

              <div style={styles.databaseIcon}>
                DB
              </div>
            </div>

            <div style={styles.databaseGrid}>

              <MiniStat
                title="Users"
                value={databaseStats?.users}
                icon="●"
              />

              <MiniStat
                title="Repositories"
                value={
                  databaseStats?.repositories
                }
                icon="◈"
              />

              <MiniStat
                title="Deployments"
                value={
                  databaseStats?.deployments
                }
                icon="▲"
              />

              <MiniStat
                title="Logs"
                value={
                  databaseStats?.deployment_logs
                }
                icon="≡"
              />

              <MiniStat
                title="Failures"
                value={
                  databaseStats?.failure_analysis
                }
                icon="!"
                danger={
                  databaseStats?.failure_analysis > 0
                }
              />

            </div>

            <div style={styles.databaseFooter}>
              <span style={styles.databaseDot}></span>

              PostgreSQL Connected

              <span style={styles.databaseStatus}>
                {databaseStats?.status ||
                  "UNKNOWN"}
              </span>
            </div>

          </section>

        </div>

        {/* ====================================================
            DEPLOYMENT HISTORY
        ==================================================== */}

        <section style={styles.panel}>

          <div style={styles.panelHeader}>
            <div>
              <h2 style={styles.panelTitle}>
                Deployment History
              </h2>

              <p style={styles.panelSubtitle}>
                Recent deployment activity
              </p>
            </div>

            <div style={styles.countBadge}>
              {deployments.length} deployments
            </div>
          </div>

          {deployments.length === 0 ? (
            <div style={styles.emptyBox}>
              No deployments found.
            </div>
          ) : (
            <div style={styles.tableWrapper}>

              <table style={styles.table}>

                <thead>
                  <tr>
                    <th style={styles.tableHeader}>
                      ID
                    </th>

                    <th style={styles.tableHeader}>
                      Repository
                    </th>

                    <th style={styles.tableHeader}>
                      Branch
                    </th>

                    <th style={styles.tableHeader}>
                      Commit
                    </th>

                    <th style={styles.tableHeader}>
                      Status
                    </th>

                    <th style={styles.tableHeader}>
                      Started
                    </th>

                    <th style={styles.tableHeader}>
                      Completed
                    </th>
                  </tr>
                </thead>

                <tbody>

                  {deployments.map(
                    (deployment) => (
                      <tr
                        key={deployment.id}
                        style={styles.tableRow}
                      >

                        <td style={styles.tableCell}>
                          <span style={styles.idBadge}>
                            #{deployment.id}
                          </span>
                        </td>

                        <td style={styles.tableCell}>
                          {deployment.repository ||
                            "Unknown"}
                        </td>

                        <td style={styles.tableCell}>
                          <span style={styles.branchBadge}>
                            {deployment.branch ||
                              "Unknown"}
                          </span>
                        </td>

                        <td
                          style={{
                            ...styles.tableCell,
                            fontFamily:
                              "monospace",
                            fontSize: "12px",
                          }}
                        >
                          {deployment.commit_id
                            ? deployment.commit_id.slice(
                                0,
                                10
                              )
                            : "N/A"}
                        </td>

                        <td style={styles.tableCell}>

                          <StatusBadge
                            status={
                              deployment.status
                            }
                            getStatusColor={
                              getStatusColor
                            }
                            getStatusBackground={
                              getStatusBackground
                            }
                          />

                        </td>

                        <td style={styles.tableCell}>
                          {formatDate(
                            deployment.started_at
                          )}
                        </td>

                        <td style={styles.tableCell}>
                          {formatDate(
                            deployment.completed_at
                          )}
                        </td>

                      </tr>
                    )
                  )}

                </tbody>

              </table>

            </div>
          )}

        </section>

        {/* ====================================================
            FAILURE ANALYSIS
        ==================================================== */}

        <section style={styles.panel}>

          <div style={styles.panelHeader}>

            <div>
              <h2 style={styles.panelTitle}>
                Failure Analysis
              </h2>

              <p style={styles.panelSubtitle}>
                CI/CD failure diagnostics
              </p>
            </div>

            <div
              style={{
                ...styles.countBadge,
                background:
                  failures.length > 0
                    ? "#fee2e2"
                    : "#dcfce7",
                color:
                  failures.length > 0
                    ? "#dc2626"
                    : "#15803d",
              }}
            >
              {failures.length} failures
            </div>

          </div>

          {failures.length === 0 ? (

            <div style={styles.successBox}>

              <div style={styles.successIcon}>
                ✓
              </div>

              <div>
                <strong>
                  No CI/CD failures recorded
                </strong>

                <p style={styles.successText}>
                  Your pipeline is currently healthy.
                </p>
              </div>

            </div>

          ) : (

            <div>

              {failures.map((failure) => (

                <div
                  key={failure.id}
                  style={styles.failureCard}
                >

                  <div style={styles.failureTop}>

                    <span style={styles.failureBadge}>
                      FAILURE
                    </span>

                    <span>
                      Deployment #
                      {failure.deployment_id}
                    </span>

                  </div>

                  <p>
                    <strong>
                      Failure Type:
                    </strong>{" "}
                    {failure.failure_type}
                  </p>

                  <p>
                    <strong>
                      Error:
                    </strong>{" "}
                    {failure.error_message}
                  </p>

                  <div style={styles.fixBox}>
                    <strong>
                      Suggested Fix
                    </strong>

                    <p>
                      {failure.suggested_fix}
                    </p>
                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

        {/* ====================================================
            BACKEND CONNECTION
        ==================================================== */}

        <section style={styles.backendPanel}>

          <div>

            <div style={styles.backendTitle}>
              Backend Connection
            </div>

            <div style={styles.backendDescription}>
              Test connectivity with the Flask API
            </div>

          </div>

          <button
            onClick={testBackend}
            disabled={backendLoading}
            style={{
              ...styles.backendButton,
              opacity: backendLoading
                ? 0.7
                : 1,
            }}
          >
            {backendLoading
              ? "Testing..."
              : "Test Backend"}
          </button>

        </section>

        {/* ====================================================
            FOOTER
        ==================================================== */}

        <footer style={styles.footer}>
          <span>
            Cloud-ByteXL
          </span>

          <span>
            DevOps Monitoring System
          </span>

          <span>
            Flask + React + PostgreSQL
          </span>
        </footer>

      </div>
    </div>
  );
}

// ============================================================
// STATUS CARD
// ============================================================

function StatusCard({
  title,
  value,
  icon,
  color,
  background,
}) {
  return (
    <div
      style={{
        ...styles.statusCard,
        background,
      }}
    >

      <div style={styles.statusCardTop}>

        <div
          style={{
            ...styles.statusIcon,
            color,
          }}
        >
          {icon}
        </div>

        <span style={styles.statusCardLabel}>
          {title}
        </span>

      </div>

      <div
        style={{
          ...styles.statusValue,
          color,
        }}
      >
        {value}
      </div>

    </div>
  );
}

// ============================================================
// STATUS BADGE
// ============================================================

function StatusBadge({
  status,
  getStatusColor,
  getStatusBackground,
}) {
  return (
    <span
      style={{
        ...styles.statusBadge,
        color: getStatusColor(status),
        background: getStatusBackground(status),
      }}
    >
      <span
        style={{
          ...styles.statusBadgeDot,
          background: getStatusColor(status),
        }}
      ></span>

      {status || "UNKNOWN"}
    </span>
  );
}

// ============================================================
// INFO CARD
// ============================================================

function InfoCard({ title, value }) {
  return (
    <div style={styles.infoCard}>

      <div style={styles.infoLabel}>
        {title}
      </div>

      <div style={styles.infoValue}>
        {value}
      </div>

    </div>
  );
}

// ============================================================
// DATABASE MINI STAT
// ============================================================

function MiniStat({
  title,
  value,
  icon,
  danger,
}) {
  return (
    <div style={styles.miniStat}>

      <div
        style={{
          ...styles.miniIcon,
          color: danger
            ? "#dc2626"
            : "#2563eb",
        }}
      >
        {icon}
      </div>

      <div>

        <div style={styles.miniLabel}>
          {title}
        </div>

        <div
          style={{
            ...styles.miniValue,
            color: danger
              ? "#dc2626"
              : "#111827",
          }}
        >
          {value ?? 0}
        </div>

      </div>

    </div>
  );
}

// ============================================================
// LOADING TEXT
// ============================================================

function LoadingText({ text }) {
  return (
    <div style={styles.loadingBox}>
      <div style={styles.spinner}></div>

      {text}
    </div>
  );
}

// ============================================================
// DATE FORMAT
// ============================================================

function formatDate(date) {
  if (!date) {
    return "N/A";
  }

  try {
    return new Date(date).toLocaleString();
  } catch {
    return "N/A";
  }
}

// ============================================================
// STYLES
// ============================================================

const styles = {
  page: {
    minHeight: "100vh",
    background:
      "linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #eff6ff 100%)",
    padding: "35px 20px",
    fontFamily:
      "Inter, Arial, Helvetica, sans-serif",
    color: "#111827",
    position: "relative",
    overflow: "hidden",
  },

  container: {
    maxWidth: "1250px",
    margin: "0 auto",
    position: "relative",
    zIndex: 2,
  },

  backgroundOrbOne: {
    position: "fixed",
    width: "350px",
    height: "350px",
    borderRadius: "50%",
    background:
      "rgba(99,102,241,0.08)",
    top: "-150px",
    right: "-100px",
    filter: "blur(5px)",
  },

  backgroundOrbTwo: {
    position: "fixed",
    width: "300px",
    height: "300px",
    borderRadius: "50%",
    background:
      "rgba(59,130,246,0.07)",
    bottom: "-120px",
    left: "-100px",
    filter: "blur(5px)",
  },

  header: {
    background: "rgba(255,255,255,0.94)",
    backdropFilter: "blur(12px)",
    borderRadius: "18px",
    padding: "24px 28px",
    marginBottom: "20px",
    boxShadow:
      "0 10px 35px rgba(15,23,42,0.08)",
    border: "1px solid rgba(255,255,255,0.8)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "20px",
    flexWrap: "wrap",
  },

  logoRow: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
  },

  logo: {
    width: "50px",
    height: "50px",
    borderRadius: "14px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background:
      "linear-gradient(135deg, #4f46e5, #2563eb)",
    color: "#fff",
    fontWeight: "800",
    fontSize: "17px",
    boxShadow:
      "0 8px 20px rgba(37,99,235,0.25)",
  },

  title: {
    margin: 0,
    fontSize: "30px",
    fontWeight: "800",
    letterSpacing: "-0.8px",
  },

  subtitle: {
    margin: "5px 0 0",
    color: "#64748b",
    fontSize: "14px",
  },

  primaryButton: {
    border: "none",
    borderRadius: "10px",
    padding: "12px 18px",
    background:
      "linear-gradient(135deg, #1e293b, #334155)",
    color: "#fff",
    fontWeight: "700",
    boxShadow:
      "0 7px 18px rgba(15,23,42,0.18)",
    transition:
      "transform 0.2s ease, box-shadow 0.2s ease",
  },

  buttonIcon: {
    marginRight: "7px",
    fontSize: "17px",
  },

  messageBox: {
    background: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "11px",
    padding: "12px 16px",
    marginBottom: "22px",
    display: "flex",
    alignItems: "center",
    gap: "9px",
    color: "#475569",
    boxShadow:
      "0 4px 14px rgba(15,23,42,0.04)",
  },

  messageDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "#22c55e",
  },

  sectionHeading: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-end",
    gap: "15px",
    marginBottom: "14px",
  },

  sectionTitle: {
    margin: 0,
    fontSize: "22px",
  },

  sectionSubtitle: {
    margin: "5px 0 0",
    color: "#64748b",
    fontSize: "13px",
  },

  statusGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(210px, 1fr))",
    gap: "14px",
  },

  statusCard: {
    borderRadius: "15px",
    padding: "20px",
    border: "1px solid rgba(226,232,240,0.9)",
    boxShadow:
      "0 7px 22px rgba(15,23,42,0.06)",
    transition:
      "transform 0.2s ease, box-shadow 0.2s ease",
  },

  statusCardTop: {
    display: "flex",
    alignItems: "center",
    gap: "9px",
  },

  statusIcon: {
    fontSize: "18px",
    fontWeight: "800",
  },

  statusCardLabel: {
    color: "#64748b",
    fontSize: "13px",
    fontWeight: "600",
  },

  statusValue: {
    fontSize: "25px",
    fontWeight: "800",
    marginTop: "12px",
  },

  statusBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "7px",
    padding: "7px 11px",
    borderRadius: "999px",
    fontSize: "12px",
    fontWeight: "800",
  },

  statusBadgeDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
  },

  workflowCard: {
    marginTop: "14px",
    background: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "13px",
    padding: "16px 18px",
    display: "flex",
    alignItems: "center",
    gap: "13px",
    boxShadow:
      "0 5px 18px rgba(15,23,42,0.05)",
    flexWrap: "wrap",
  },

  workflowIcon: {
    width: "38px",
    height: "38px",
    borderRadius: "10px",
    background: "#eef2ff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#4f46e5",
  },

  smallLabel: {
    fontSize: "10px",
    color: "#94a3b8",
    fontWeight: "800",
    letterSpacing: "0.8px",
  },

  workflowName: {
    marginTop: "2px",
    fontWeight: "700",
  },

  workflowLine: {
    flex: 1,
    minWidth: "30px",
    height: "1px",
    background: "#e2e8f0",
  },

  workflowStatus: {
    color: "#16a34a",
    fontSize: "13px",
    fontWeight: "700",
  },

  twoColumnGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(400px, 1fr))",
    gap: "20px",
    marginTop: "22px",
  },

  panel: {
    background: "rgba(255,255,255,0.96)",
    borderRadius: "16px",
    padding: "23px",
    marginTop: "22px",
    boxShadow:
      "0 8px 28px rgba(15,23,42,0.06)",
    border: "1px solid #e5e7eb",
  },

  panelHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "15px",
    marginBottom: "18px",
  },

  panelTitle: {
    margin: 0,
    fontSize: "20px",
    fontWeight: "750",
  },

  panelSubtitle: {
    margin: "5px 0 0",
    color: "#64748b",
    fontSize: "13px",
  },

  githubIcon: {
    background: "#111827",
    color: "#ffffff",
    borderRadius: "9px",
    padding: "9px 11px",
    fontSize: "11px",
    fontWeight: "800",
  },

  databaseIcon: {
    background: "#eff6ff",
    color: "#2563eb",
    borderRadius: "9px",
    padding: "9px 11px",
    fontSize: "11px",
    fontWeight: "800",
  },

  infoGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(2, minmax(0, 1fr))",
    gap: "10px",
  },

  infoCard: {
    background: "#f8fafc",
    borderRadius: "10px",
    padding: "13px",
    border: "1px solid #e2e8f0",
  },

  infoLabel: {
    color: "#94a3b8",
    fontSize: "11px",
    fontWeight: "700",
    marginBottom: "5px",
    textTransform: "uppercase",
  },

  infoValue: {
    fontSize: "14px",
    fontWeight: "700",
    wordBreak: "break-word",
  },

  commitCard: {
    marginTop: "13px",
    background: "#f8fafc",
    borderRadius: "11px",
    padding: "16px",
    border: "1px solid #e2e8f0",
  },

  commitHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },

  commitTitle: {
    margin: 0,
    fontSize: "15px",
  },

  commitBadge: {
    fontSize: "9px",
    fontWeight: "800",
    padding: "5px 7px",
    borderRadius: "6px",
    background: "#e0e7ff",
    color: "#4338ca",
  },

  commitMessage: {
    fontSize: "14px",
    lineHeight: "1.5",
    color: "#334155",
  },

  commitDetails: {
    display: "flex",
    gap: "30px",
    flexWrap: "wrap",
  },

  detailLabel: {
    display: "block",
    fontSize: "10px",
    color: "#94a3b8",
    fontWeight: "700",
    textTransform: "uppercase",
    marginBottom: "4px",
  },

  commitId: {
    fontFamily: "monospace",
    fontSize: "12px",
    color: "#475569",
  },

  detailValue: {
    fontSize: "13px",
    fontWeight: "600",
  },

  databaseGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(2, minmax(0, 1fr))",
    gap: "10px",
  },

  miniStat: {
    display: "flex",
    alignItems: "center",
    gap: "11px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "10px",
    padding: "14px",
  },

  miniIcon: {
    width: "32px",
    height: "32px",
    borderRadius: "8px",
    background: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: "800",
    boxShadow:
      "0 2px 7px rgba(15,23,42,0.06)",
  },

  miniLabel: {
    color: "#64748b",
    fontSize: "11px",
  },

  miniValue: {
    fontSize: "20px",
    fontWeight: "800",
    marginTop: "2px",
  },

  databaseFooter: {
    marginTop: "14px",
    padding: "11px 13px",
    borderRadius: "9px",
    background: "#f0fdf4",
    color: "#15803d",
    fontSize: "12px",
    fontWeight: "700",
    display: "flex",
    alignItems: "center",
    gap: "7px",
  },

  databaseDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    background: "#22c55e",
  },

  databaseStatus: {
    marginLeft: "auto",
  },

  countBadge: {
    background: "#eef2ff",
    color: "#4338ca",
    padding: "7px 10px",
    borderRadius: "999px",
    fontSize: "11px",
    fontWeight: "800",
  },

  tableWrapper: {
    overflowX: "auto",
    border: "1px solid #e2e8f0",
    borderRadius: "10px",
  },

  table: {
    width: "100%",
    borderCollapse: "collapse",
    minWidth: "800px",
  },

  tableHeader: {
    padding: "13px 12px",
    background: "#f8fafc",
    borderBottom: "1px solid #e2e8f0",
    textAlign: "left",
    fontSize: "11px",
    color: "#64748b",
    fontWeight: "800",
    textTransform: "uppercase",
  },

  tableRow: {
    transition:
      "background 0.15s ease",
  },

  tableCell: {
    padding: "13px 12px",
    borderBottom: "1px solid #f1f5f9",
    fontSize: "12px",
    color: "#475569",
  },

  idBadge: {
    background: "#f1f5f9",
    padding: "5px 8px",
    borderRadius: "6px",
    fontWeight: "700",
    color: "#334155",
  },

  branchBadge: {
    background: "#eff6ff",
    color: "#2563eb",
    padding: "5px 8px",
    borderRadius: "6px",
    fontSize: "11px",
    fontWeight: "700",
  },

  successBox: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    background: "#f0fdf4",
    border: "1px solid #bbf7d0",
    color: "#15803d",
    padding: "16px",
    borderRadius: "10px",
  },

  successIcon: {
    width: "35px",
    height: "35px",
    borderRadius: "50%",
    background: "#dcfce7",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: "900",
  },

  successText: {
    margin: "3px 0 0",
    fontSize: "12px",
    color: "#4d7c5b",
  },

  failureCard: {
    background: "#fff7f7",
    border: "1px solid #fecaca",
    borderRadius: "11px",
    padding: "17px",
    marginBottom: "12px",
    color: "#374151",
  },

  failureTop: {
    display: "flex",
    justifyContent: "space-between",
    gap: "10px",
    marginBottom: "10px",
    fontSize: "12px",
    color: "#64748b",
  },

  failureBadge: {
    background: "#fee2e2",
    color: "#dc2626",
    padding: "5px 8px",
    borderRadius: "6px",
    fontSize: "10px",
    fontWeight: "800",
  },

  fixBox: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "12px",
    marginTop: "12px",
    fontSize: "13px",
  },

  emptyBox: {
    background: "#f8fafc",
    border: "1px dashed #cbd5e1",
    borderRadius: "10px",
    padding: "25px",
    textAlign: "center",
    color: "#64748b",
  },

  loadingBox: {
    minHeight: "120px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    color: "#64748b",
    fontSize: "13px",
  },

  spinner: {
    width: "16px",
    height: "16px",
    border: "2px solid #dbeafe",
    borderTop: "2px solid #2563eb",
    borderRadius: "50%",
    animation:
      "spin 1s linear infinite",
  },

  backendPanel: {
    marginTop: "22px",
    background:
      "linear-gradient(135deg, #111827, #1e293b)",
    borderRadius: "16px",
    padding: "22px 24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "20px",
    flexWrap: "wrap",
    boxShadow:
      "0 10px 30px rgba(15,23,42,0.16)",
  },

  backendTitle: {
    color: "#ffffff",
    fontSize: "17px",
    fontWeight: "750",
  },

  backendDescription: {
    color: "#94a3b8",
    fontSize: "12px",
    marginTop: "4px",
  },

  backendButton: {
    border: "none",
    borderRadius: "9px",
    padding: "11px 17px",
    background: "#ffffff",
    color: "#111827",
    fontWeight: "750",
    cursor: "pointer",
    transition:
      "transform 0.2s ease",
  },

  footer: {
    padding: "24px 5px 5px",
    display: "flex",
    justifyContent: "space-between",
    gap: "15px",
    flexWrap: "wrap",
    color: "#94a3b8",
    fontSize: "11px",
  },
};

export default App;