// Sentiment is inherently a good/bad/critical state, so it draws from the
// dataviz skill's reserved status palette rather than arbitrary categorical
// hues; neutral uses the palette's muted chrome gray since it isn't a status.
export const SENTIMENT_COLORS = {
  positive: "#0ca30c",
  neutral: "#898781",
  negative: "#d03b3b",
  mixed: "#ec835a",
};

// Platforms are nominal categorical identity (order-free), so each gets a
// fixed slot from the dataviz skill's validated 8-hue categorical order,
// reused consistently across every chart in the app.
export const PLATFORM_COLORS = {
  linkedin: "#2a78d6", // slot 1 blue
  reddit: "#eb6834", // slot 2 orange
  facebook: "#1baf7a", // slot 3 aqua
  instagram: "#eda100", // slot 4 yellow
};

export const PLATFORM_LABELS = {
  linkedin: "LinkedIn",
  reddit: "Reddit",
  facebook: "Facebook",
  instagram: "Instagram",
};

export function severityLabel(score) {
  if (score === null || score === undefined) return null;
  if (score <= 30) return "LOW";
  if (score <= 60) return "MEDIUM";
  if (score <= 80) return "HIGH";
  return "CRITICAL";
}

export const SEVERITY_COLORS = {
  LOW: "#65a30d",
  MEDIUM: "#d97706",
  HIGH: "#ea580c",
  CRITICAL: "#dc2626",
};

export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
