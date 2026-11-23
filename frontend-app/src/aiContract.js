export const reviewFields = ["category_correct", "step_correct", "evidence_correct", "fix_correct", "unsupported_claims"];
export const emptyReview = () => Object.fromEntries(reviewFields.map(key => [key, ""]));
export const percent = value => typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "Unavailable";
export const fixed = (value, digits = 4) => typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "Unavailable";
export const date = value => value && Number.isFinite(new Date(value).getTime()) ? new Date(value).toLocaleString() : "Unavailable";

export function reviewPayload(review, reviewer, acknowledged) {
  if (!reviewer.trim() || !acknowledged || !reviewFields.every(key => ["true", "false"].includes(review[key]))) return null;
  return { reviewer: reviewer.trim(), ...Object.fromEntries(reviewFields.map(key => [key, review[key] === "true"])) };
}

export function shadowRecord(predictions = []) {
  // This selects stored shadow rows, not independently verified prospective evidence.
  return predictions.find(row => row.mode === "shadow" && ["pending", "matched"].includes(row.verification_status));
}

export function guardStatus(report = {}) {
  const statuses = [report.validation?.status, report.final_guard?.status, report.live_validation?.final_guard?.status];
  if (statuses.includes("rejected")) return "rejected";
  return statuses.find(Boolean) || "not evaluated";
}
