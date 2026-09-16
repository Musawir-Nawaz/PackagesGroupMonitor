import { useEffect, useState } from "react";
import { getSentimentBreakdown, runCollection } from "../services/api";
import { PLATFORM_LABELS, SENTIMENT_COLORS } from "../utils/format";

const PLATFORMS = ["reddit", "linkedin", "facebook", "instagram"];

function Platforms() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(null); // platform currently collecting, or null
  const [results, setResults] = useState({}); // platform -> last run result/error

  const refresh = () => getSentimentBreakdown().then(setData);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  const handleRun = async (platform) => {
    setRunning(platform);
    setResults((r) => ({ ...r, [platform]: null }));
    try {
      const run = await runCollection(platform);
      setResults((r) => ({ ...r, [platform]: { ok: true, ...run } }));
      await refresh();
    } catch (err) {
      setResults((r) => ({ ...r, [platform]: { ok: false, error: err.message || "Collection failed" } }));
    } finally {
      setRunning(null);
    }
  };

  const rows = data?.by_platform || [];

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">Platform comparison</h2>
      <p className="text-sm text-slate-500">
        Where reputation issues are concentrated, at a glance — each row is one platform's sentiment mix.
      </p>

      <div className="bg-white rounded-lg border border-slate-200 p-4">
     
        <div className="flex flex-wrap gap-2">
          {PLATFORMS.map((p) => (
            <button
              key={p}
              onClick={() => handleRun(p)}
              disabled={running !== null}
              className="px-3 py-1.5 text-xs font-medium rounded border border-slate-300 bg-slate-800 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-700"
            >
              {running === p ? `Collecting ${PLATFORM_LABELS[p]}…` : `Run ${PLATFORM_LABELS[p]}`}
            </button>
          ))}
        </div>
        <div className="mt-3 space-y-1">
          {PLATFORMS.map((p) =>
            results[p] ? (
              <p key={p} className={`text-xs ${results[p].ok ? "text-slate-600" : "text-red-600"}`}>
                {PLATFORM_LABELS[p]}:{" "}
                {results[p].ok
                  ? `${results[p].items_new} new, ${results[p].items_duplicate} duplicate (${results[p].items_collected} fetched)`
                  : results[p].error}
              </p>
            ) : null
          )}
        </div>
      </div>

      {!loading && rows.length === 0 && <p className="text-sm text-slate-500">No analyzed comments yet.</p>}

      {!loading && rows.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-2">Platform</th>
                <th className="text-left px-4 py-2 w-1/2">Sentiment mix</th>
                <th className="text-right px-4 py-2">Positive</th>
                <th className="text-right px-4 py-2">Neutral</th>
                <th className="text-right px-4 py-2">Negative</th>
                <th className="text-right px-4 py-2">Mixed</th>
                <th className="text-right px-4 py-2">Mentions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.platform} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {PLATFORM_LABELS[row.platform] || row.platform}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex h-3 rounded overflow-hidden bg-slate-100">
                      {["positive", "neutral", "negative", "mixed"].map((s) => (
                        <div
                          key={s}
                          style={{ width: `${row[`${s}_pct`]}%`, backgroundColor: SENTIMENT_COLORS[s] }}
                          title={`${s}: ${row[`${s}_pct`]}%`}
                        />
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right" style={{ color: SENTIMENT_COLORS.positive }}>
                    {row.positive_pct}%
                  </td>
                  <td className="px-4 py-3 text-right text-slate-500">{row.neutral_pct}%</td>
                  <td className="px-4 py-3 text-right" style={{ color: SENTIMENT_COLORS.negative }}>
                    {row.negative_pct}%
                  </td>
                  <td className="px-4 py-3 text-right" style={{ color: SENTIMENT_COLORS.mixed }}>
                    {row.mixed_pct}%
                  </td>
                  <td className="px-4 py-3 text-right text-slate-800">{row.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Platforms;
