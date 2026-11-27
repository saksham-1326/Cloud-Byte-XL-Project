// Public read-only demo supports one explicitly authorized repository.
// Do not call the backend with arbitrary untrusted repository identifiers.
export const DEMO_REPOSITORY = "saksham-1326/Cloud-Byte-XL-Project";
export const DEMO_REPOSITORY_URL = `https://github.com/${DEMO_REPOSITORY}`;

export function normalizeRepositoryUrl(value) {
  if (typeof value !== "string") throw new Error("Enter a GitHub repository URL.");
  const raw = value.trim();
  if (!raw) throw new Error("Enter a GitHub repository URL.");
  const candidate = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  let url;
  try { url = new URL(candidate); } catch { throw new Error("Enter a valid GitHub repository URL."); }
  if (url.protocol !== "https:" || !["github.com", "www.github.com"].includes(url.hostname.toLowerCase())
      || url.username || url.password || url.search || url.hash || url.port) {
    throw new Error("Use a standard HTTPS github.com/owner/repository URL.");
  }
  const parts = url.pathname.replace(/\/$/, "").replace(/\.git$/i, "").split("/").filter(Boolean);
  if (parts.length !== 2 || !parts.every(part => /^[a-zA-Z0-9_.-]+$/.test(part))) {
    throw new Error("GitHub URL must have an owner and repository name.");
  }
  return `https://github.com/${parts[0]}/${parts[1]}`;
}

export function validateDemoRepository(value) {
  const normalized = normalizeRepositoryUrl(value);
  if (normalized.toLowerCase() !== DEMO_REPOSITORY_URL.toLowerCase()) {
    throw new Error(`This public read-only demo only permits ${DEMO_REPOSITORY}. Select the demo repository; scanning others requires a separately authenticated deployment.`);
  }
  return DEMO_REPOSITORY_URL;
}
