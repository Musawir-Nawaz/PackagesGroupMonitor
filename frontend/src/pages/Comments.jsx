import { useEffect, useState } from "react";
import CommentCard from "../components/CommentCard";
import { getComments } from "../services/api";
import { PLATFORM_LABELS, formatDateTime, severityLabel } from "../utils/format";

const PLATFORMS = ["linkedin", "reddit", "facebook", "instagram"];
const SENTIMENTS = ["positive", "neutral", "negative", "mixed"];
const SEVERITY_OPTIONS = [
  { label: "Any severity", value: "" },
  { label: "High risk (60+)", value: "61" },
  { label: "Critical (80+)", value: "81" },
];

function Comments() {
  const [filters, setFilters] = useState({
    platform: "",
    sentiment: "",
    severity_min: "",
    search: "",
    relevant_only: false,
  });
  const [result, setResult] = useState({ total: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    setLoading(true);
    const timeout = setTimeout(() => {
      getComments({ ...filters, limit: 50 })
        .then(setResult)
        .catch(() => setResult({ total: 0, items: [] }))
        .finally(() => setLoading(false));
    }, 250); // debounce the free-text search field
    return () => clearTimeout(timeout);
  }, [filters]);

  const updateFilter = (key, value) => setFilters((f) => ({ ...f, [key]: value }));

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">Comments</h2>

      <div className="flex flex-wrap gap-2 bg-white border border-slate-200 rounded-lg p-3">
        <select
          className="text-sm border border-slate-300 rounded px-2 py-1.5"
          value={filters.platform}
          onChange={(e) => updateFilter("platform", e.target.value)}
        >
          <option value="">All platforms</option>
          {PLATFORMS.map((p) => (
            <option key={p} value={p}>
              {PLATFORM_LABELS[p]}
            </option>
          ))}
        </select>
        <select
          className="text-sm border border-slate-300 rounded px-2 py-1.5"
          value={filters.sentiment}
          onChange={(e) => updateFilter("sentiment", e.target.value)}
        >
          <option value="">All sentiment</option>
          {SENTIMENTS.map((s) => (
            <option key={s} value={s}>
              {s[0].toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        <select
          className="text-sm border border-slate-300 rounded px-2 py-1.5"
          value={filters.severity_min}
          onChange={(e) => updateFilter("severity_min", e.target.value)}
        >
          {SEVERITY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="Search text..."
          className="text-sm border border-slate-300 rounded px-2 py-1.5 flex-1 min-w-[160px]"
          value={filters.search}
          onChange={(e) => updateFilter("search", e.target.value)}
        />
        <label className="flex items-center gap-1.5 text-sm text-slate-600 px-2 whitespace-nowrap">
          <input
            type="checkbox"
            checked={filters.relevant_only}
            onChange={(e) => updateFilter("relevant_only", e.target.checked)}
          />
          Relevant only
        </label>
      </div>

      <p className="text-xs text-slate-500">
        {loading
          ? "Loading..."
          : `${result.total} comment(s)${filters.relevant_only ? "" : " (includes items not flagged as relevant — check \"Relevant only\" to narrow down)"}`}
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-2">
          {result.items.map((c) => (
            <button key={c.id} onClick={() => setSelected(c)} className="block w-full text-left">
              <CommentCard comment={c} />
            </button>
          ))}
          {!loading && result.items.length === 0 && (
            <p className="text-sm text-slate-500">No comments match these filters.</p>
          )}
        </div>

        {selected && (
          <div className="bg-white rounded-lg border border-slate-200 p-4 h-fit sticky top-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-700">Comment detail</h3>
              <button onClick={() => setSelected(null)} className="text-xs text-slate-400 hover:text-slate-600">
                Close
              </button>
            </div>
            <dl className="text-sm space-y-2">
              <Detail label="Text" value={selected.text} />
              <Detail label="Platform" value={PLATFORM_LABELS[selected.platform] || selected.platform} />
              <Detail label="Source" value={selected.source_type} />
              <Detail label="Author" value={selected.author_name} />
              <Detail label="Date" value={formatDateTime(selected.created_at)} />
              <Detail label="Sentiment" value={selected.sentiment} />
              <Detail label="Confidence" value={selected.confidence ? `${Math.round(selected.confidence * 100)}%` : "—"} />
              <Detail label="Severity" value={selected.severity != null ? `${severityLabel(selected.severity)} (${selected.severity})` : "—"} />
              <Detail label="Topic" value={selected.topic} />
              <Detail label="Engagement" value={selected.engagement} />
              <Detail
                label="Original URL"
                value={
                  selected.comment_url || selected.post_url ? (
                    <a
                      href={selected.comment_url || selected.post_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      Open
                    </a>
                  ) : (
                    "—"
                  )
                }
              />
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-slate-500 uppercase tracking-wide">{label}</dt>
      <dd className="text-slate-800">{value || "—"}</dd>
    </div>
  );
}

export default Comments;
