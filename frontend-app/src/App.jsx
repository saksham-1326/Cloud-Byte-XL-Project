import { useEffect, useState } from "react";
// CI/CD integration test
const BACKEND_URL = "http://127.0.0.1:5000";

function App() {
  const [message, setMessage] = useState("");
  const [githubData, setGithubData] = useState(null);
  const [ciData, setCiData] = useState(null);
  const [loading, setLoading] = useState(false);

  const testBackend = async () => {
    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(`${BACKEND_URL}/`);

      if (!response.ok) {
        throw new Error("Backend returned an error");
      }

      const data = await response.json();
      setMessage(data.message);
    } catch (error) {
      console.error(error);
      setMessage("Could not connect to Flask backend.");
    } finally {
      setLoading(false);
    }
  };

  const getGithubData = async () => {
    setLoading(true);

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/github/latest`
      );

      if (!response.ok) {
        throw new Error("Could not fetch GitHub data");
      }

      const data = await response.json();

      setGithubData(data);
      setMessage("");
    } catch (error) {
      console.error(error);
      setMessage("Could not fetch GitHub data.");
    } finally {
      setLoading(false);
    }
  };

  const getCIStatus = async () => {
    try {
      const response = await fetch(
        `${BACKEND_URL}/api/ci/status`
      );

      if (!response.ok) {
        throw new Error("Could not fetch CI/CD status");
      }

      const data = await response.json();

      setCiData(data);
    } catch (error) {
      console.error(error);
    }
  };

  // Load data when page opens
  useEffect(() => {
    getGithubData();
    getCIStatus();
  }, []);

  return (
    <div
      style={{
        padding: "40px",
        fontFamily: "Arial, sans-serif",
        maxWidth: "900px",
        margin: "auto",
      }}
    >
      <h1>Cloud-ByteXL</h1>

      <p>Frontend is running successfully! 🚀</p>

      <div style={{ marginBottom: "20px" }}>
        <button onClick={testBackend} disabled={loading}>
          {loading ? "Connecting..." : "Test Backend"}
        </button>

        <button
          onClick={getGithubData}
          disabled={loading}
          style={{ marginLeft: "10px" }}
        >
          {loading
            ? "Loading..."
            : "Refresh GitHub Activity"}
        </button>

        <button
          onClick={getCIStatus}
          style={{ marginLeft: "10px" }}
        >
          Refresh CI/CD Status
        </button>
      </div>

      {message && (
        <div
          style={{
            padding: "15px",
            marginTop: "20px",
            border: "1px solid #ccc",
            borderRadius: "8px",
          }}
        >
          {message}
        </div>
      )}

      {/* CI/CD STATUS */}

      {ciData && (
        <div
          style={{
            marginTop: "30px",
            padding: "25px",
            border: "1px solid #ddd",
            borderRadius: "10px",
          }}
        >
          <h2>CI/CD Pipeline Status</h2>

          <p>
            <strong>Workflow:</strong>{" "}
            {ciData.workflow || "Unknown"}
          </p>

          <p>
            <strong>Overall Status:</strong>{" "}
            <span
              style={{
                fontWeight: "bold",
                color:
                  ciData.status === "SUCCESS"
                    ? "green"
                    : "red",
              }}
            >
              {ciData.status || "UNKNOWN"}
            </span>
          </p>

          <p>
            <strong>Build:</strong>{" "}
            {ciData.build || "UNKNOWN"}
          </p>

          <p>
            <strong>Tests:</strong>{" "}
            {ciData.tests || "UNKNOWN"}
          </p>

          <p>
            <strong>Docker:</strong>{" "}
            {ciData.docker || "UNKNOWN"}
          </p>
        </div>
      )}

      {/* GITHUB ACTIVITY */}

      {githubData && (
        <div
          style={{
            marginTop: "30px",
            padding: "25px",
            border: "1px solid #ddd",
            borderRadius: "10px",
          }}
        >
          <h2>Latest GitHub Activity</h2>

          <p>
            <strong>Repository:</strong>{" "}
            {githubData.repository || "Unknown"}
          </p>

          <p>
            <strong>Branch:</strong>{" "}
            {githubData.branch || "Unknown"}
          </p>

          <p>
            <strong>Event:</strong>{" "}
            {githubData.event || "Unknown"}
          </p>

          <p>
            <strong>Pusher:</strong>{" "}
            {githubData.pusher || "Unknown"}
          </p>

          <h3>Latest Commit</h3>

          {githubData.commits &&
          githubData.commits.length > 0 ? (
            <div>
              <p>
                <strong>Message:</strong>{" "}
                {githubData.commits[0].message ||
                  "No message"}
              </p>

              <p>
                <strong>Commit ID:</strong>{" "}
                {githubData.commits[0].id ||
                  "Unknown"}
              </p>

              <p>
                <strong>Author:</strong>{" "}
                {githubData.commits[0].author?.name ||
                  "Unknown"}
              </p>
            </div>
          ) : (
            <p>No commit information available.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;