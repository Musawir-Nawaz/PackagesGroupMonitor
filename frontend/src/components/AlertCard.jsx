import { PLATFORM_LABELS, SEVERITY_COLORS, formatDateTime } from "../utils/format";

function AlertCard({ alert }) {
  const comment = alert.comment;
  const url = comment?.comment_url || comment?.post_url;
  const isCritical = alert.alert_type === "critical";

  return (
    <div className={`bg-white rounded-lg border p-4 ${isCritical ? "border-red-300" : "border-orange-300"}`}>
      <div className="flex items-center gap-2 flex-wrap text-xs mb-2">
        <span
          className="px-2 py-0.5 rounded font-semibold text-white"
          style={{ backgroundColor: SEVERITY_COLORS[alert.severity] || "#898781" }}
        >
          {isCritical ? "CRITICAL" : "HIGH RISK"}
        </span>
        {comment && (
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
            {PLATFORM_LABELS[comment.platform] || comment.platform}
          </span>
        )}
        <span className="text-slate-400 ml-auto">{formatDateTime(alert.created_at)}</span>
      </div>
      <p className="text-sm text-slate-800 leading-relaxed">{comment?.text || alert.message}</p>
      {url && (
        <a href={url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline mt-2 inline-block">
          Open original
        </a>
      )}
    </div>
  );
}

export default AlertCard;
