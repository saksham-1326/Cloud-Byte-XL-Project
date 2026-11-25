// Shared error/timeout handling for the existing Flask contracts. No secrets here.
const configuredBase = import.meta.env?.VITE_API_BASE_URL;
if (import.meta.env?.PROD) {
  const target = configuredBase ? new URL(configuredBase) : null;
  if (!target || target.protocol !== "https:" || ["localhost", "127.0.0.1", "[::1]"].includes(target.hostname) || target.username || target.password || target.search || target.hash || target.pathname !== "/") {
    throw new Error("Production requires VITE_API_BASE_URL to be an HTTPS backend origin.");
  }
}
export const API_BASE = (configuredBase || "http://127.0.0.1:5000").replace(/\/+$/, "");

export async function requestJson(url, options = {}) {
  const { signal, timeoutMs = 15000, ...init } = options;
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  else signal?.addEventListener("abort", abort, { once: true });
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    if (!response.headers.get("content-type")?.includes("application/json")) {
      throw new Error("Backend returned a non-JSON response. Check the API address and server logs.");
    }
    let result;
    try { result = await response.json(); }
    catch { throw new Error("Backend returned invalid JSON. Retry after checking the server."); }
    if (!result || typeof result !== "object" || Array.isArray(result)) throw new Error("Backend returned an invalid response contract.");
    if (!response.ok || result?.status === "FAILED") {
      throw new Error(result?.message || `Backend request failed (HTTP ${response.status}).`);
    }
    if (!["SUCCESS", "ACCEPTED"].includes(result.status)) throw new Error("Backend response is missing a supported status.");
    return result;
  } catch (error) {
    if (timedOut) throw new Error("Backend request timed out. The operation may still be running; refresh before retrying.", { cause: error });
    if (error.name === "AbortError") throw error;
    if (error instanceof TypeError) throw new Error("Cannot reach the backend. Check the configured API address and server availability.", { cause: error });
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abort);
  }
}
