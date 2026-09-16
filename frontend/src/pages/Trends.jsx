import { useEffect, useState } from "react";
import SentimentChart from "../components/SentimentChart";
import { getDashboardTrends } from "../services/api";

const PERIODS = [
  { value: "today", label: "Today" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last 90 days" },
];

function Trends() {
  const [period, setPeriod] = useState("30d");
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getDashboardTrends(period)
      .then(setTrends)
      .finally(() => setLoading(false));
  }, [period]);

  const series = trends?.series || [];
  const totals = series.reduce(
    (acc, p) => ({
      positive: acc.positive + p.positive,
      neutral: acc.neutral + p.neutral,
      negative: acc.negative + p.negative,
      mixed: acc.mixed + p.mixed,
      total: acc.total + p.total,
    }),
    { positive: 0, neutral: 0, negative: 0, mixed: 0, total: 0 }
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold text-slate-800">Sentiment trend</h2>
        <div className="flex gap-1 bg-white border border-slate-200 rounded-md p-1">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded ${
                period === p.value ? "bg-slate-800 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4">
        {!loading && <SentimentChart data={series} />}
      </div>

      <div className="flex items-baseline justify-between">
        <p className="text-xs text-slate-500">
          Totals across {PERIODS.find((p) => p.value === period)?.label.toLowerCase()} — hover a point above for that day's breakdown
        </p>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-sm">
        <SummaryTile label="Total" value={totals.total} />
        <SummaryTile label="Positive" value={totals.positive} />
        <SummaryTile label="Neutral" value={totals.neutral} />
        <SummaryTile label="Negative" value={totals.negative} />
        <SummaryTile label="Mixed" value={totals.mixed} />
      </div>
    </div>
  );
}

function SummaryTile({ label, value }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-3 text-center">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-800">{value}</p>
    </div>
  );
}

export default Trends;
