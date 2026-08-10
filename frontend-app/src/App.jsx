import { useState } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const testBackend = async () => {
    setLoading(true);
    setMessage("");

    try {
      const response = await fetch("http://127.0.0.1:5000/");
      const data = await response.text();

      setMessage(data);
    } catch (error) {
      setMessage("Could not connect to Flask backend.");
      console.error(error);
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Cloud-ByteXL</h1>

      <p>Frontend is running successfully.</p>

      <button onClick={testBackend} disabled={loading}>
        {loading ? "Connecting..." : "Test Backend"}
      </button>

      {message && (
        <pre style={{ marginTop: "20px" }}>
          {message}
        </pre>
      )}
    </div>
  );
}

export default App;