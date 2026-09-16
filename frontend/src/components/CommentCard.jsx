import { PLATFORM_LABELS, SENTIMENT_COLORS, SEVERITY_COLORS, formatDateTime, severityLabel } from "../utils/format";

function CommentCard({ comment }) {
  const label = severityLabel(comment.severity);
  const url = comment.comment_url || comment.post_url;

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="flex items-center gap-2 flex-wrap text-xs mb-2">
        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
          {PLATFORM_LABELS[comment.platform] || comment.platform}
        </span>
        {comment.sentiment && (
          <span
            className="px-2 py-0.5 rounded font-medium text-white"
            style={{ backgroundColor: SENTIMENT_COLORS[comment.sentiment] }}
          >
            {comment.sentiment}
          </span>
        )}
        {label && (
          <span
            className="px-2 py-0.5 rounded font-medium text-white"
            style={{ backgroundColor: SEVERITY_COLORS[label] }}
          >
            {label} ({comment.severity})
          </span>
        )}
        {comment.topic && <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600">{comment.topic}</span>}
        {!comment.is_relevant && (
          <span
            className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200"
            title="Didn't match the relevance keyword filter — likely a false positive from the platform search, not a genuine company mention"
          >
            not flagged relevant
          </span>
        )}
        <span className="text-slate-400 ml-auto">{formatDateTime(comment.created_at)}</span>
      </div>
      <p className="text-sm text-slate-800 leading-relaxed">{comment.text}</p>
      <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
        <span>
          {comment.author_name || "Unknown author"} &middot; {comment.engagement} engagement
        </span>
        {url && (
          <a href={url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
            Open original
          </a>
        )}
      </div>
    </div>
  );
}

export default CommentCard;
