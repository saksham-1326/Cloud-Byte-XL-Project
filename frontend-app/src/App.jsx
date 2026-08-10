import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [githubData, setGithubData] = useState(null);
  const [loading, setLoading] = useState(false);

  const testBackend = async () => {
    setLoading(true);
    setMessage("");

    try {
      const response = await fetch("http://127.0.0.1:5000/");
      const data = await response.json();

      setMessage(data.message);
    } catch (error) {
      setMessage("Could not connect to Flask backend.");
      console.error(error);
    }

    setLoading(false);
  };

  const getGithubData = async () => {
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/api/github/latest"
      );

      const data = await response.json();

      setGithubData(data);
    } catch (error) {
      console.error(error);
      setMessage("Could not fetch GitHub data.");
    }

    setLoading(false);
  };

  // Automatically load GitHub activity when the page opens
  useEffect(() => {
    getGithubData();
  }, []);

  return (
    <div
      style={{
        padding: "40px",
        fontFamily: "Arial",
        maxWidth: "900px",
        margin: "auto",
      }}
    >
      <h1>Cloud-ByteXL</h1>

      <p>Frontend is running successfully! 🚀</p>

      <button onClick={testBackend} disabled={loading}>
        {loading ? "Connecting..." : "Test Backend"}
      </button>

      <button
        onClick={getGithubData}
        disabled={loading}
        style={{ marginLeft: "10px" }}
      >
        {loading ? "Loading..." : "Refresh GitHub Activity"}
      </button>

      {message && (
        <pre style={{ marginTop: "20px" }}>
          {message}
        </pre>
      )}

      {githubData && (
        <div style={{ marginTop: "30px" }}>
          <h2>Latest GitHub Activity</h2>

          <p>
            <strong>Repository:</strong>{" "}
            {githubData.repository}
          </p>

          <p>
            <strong>Branch:</strong>{" "}
            {githubData.branch}
          </p>

          <p>
            <strong>Event:</strong>{" "}
            {githubData.event}
          </p>

          <p>
            <strong>Pusher:</strong>{" "}
            {githubData.pusher}
          </p>

          <h3>Commit</h3>

          {githubData.commits &&
            githubData.commits.length > 0 && (
              <div>
                <p>
                  <strong>Message:</strong>{" "}
                  {githubData.commits[0].message}
                </p>

                <p>
                  <strong>Commit ID:</strong>{" "}
                  {githubData.commits[0].id}
                </p>

                <p>
                  <strong>Author:</strong>{" "}
                  {githubData.commits[0].author?.name}
                </p>
              </div>
            )}
        </div>
      )}
    </div>
  );
}

export default App;