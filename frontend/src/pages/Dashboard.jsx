import { useEffect, useState } from "react";
import AlertCard from "../components/AlertCard";
import PlatformChart from "../components/PlatformChart";
import SentimentChart from "../components/SentimentChart";
import StatCard from "../components/StatCard";
import { getAlerts, getDashboardSummary, getDashboardTrends } from "../services/api";
import { SENTIMENT_COLORS } from "../utils/format";

const PERIODS = [
  { value: "today", label: "Today" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last 90 days" },
];

function Dashboard() {
  const [period, setPeriod] = useState("7d");
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [spike, setSpike] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([getDashboardSummary(period), getDashboardTrends(period), getAlerts()])
      .then(([summaryRes, trendsRes, alertsRes]) => {
        setSummary(summaryRes);
        setTrends(trendsRes);
        setSpike(alertsRes.negative_spike);
        setError(null);
      })
      .catch(() => setError("Could not reach the backend API."))
      .finally(() => setLoading(false));
  }, [period]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold text-slate-800">Overview</h2>
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

      {error && <p className="text-sm text-red-600">{error}</p>}

      {spike && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-4">
          <p className="font-semibold text-red-800">🚨 Negative sentiment spike detected</p>
          <p className="text-sm text-red-700 mt-1">
            Negative mentions increased {spike.increase_pct}% today ({spike.today_count} vs. a {spike.baseline_avg}/day
            average).{" "}
            {spike.main_topic && (
              <>
                Main topic: <strong>{spike.main_topic}</strong>.{" "}
              </>
            )}
            {spike.main_platform && (
              <>
                Main platform: <strong>{spike.main_platform}</strong>.
              </>
            )}
          </p>
        </div>
      )}

      {!loading && summary && (
        <>
          <div className="flex gap-4 flex-wrap">
            <StatCard label="Total mentions" value={summary.total_mentions} />
            <StatCard label="Positive" value={`${summary.positive_pct}%`} accent={SENTIMENT_COLORS.positive} />
            <StatCard label="Neutral" value={`${summary.neutral_pct}%`} accent={SENTIMENT_COLORS.neutral} />
            <StatCard label="Negative" value={`${summary.negative_pct}%`} accent={SENTIMENT_COLORS.negative} />
            <StatCard label="Mixed" value={`${summary.mixed_pct}%`} accent={SENTIMENT_COLORS.mixed} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Sentiment trend</h3>
              <SentimentChart data={trends?.series} />
            </div>
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Platform breakdown</h3>
              <PlatformChart data={summary.platform_breakdown} />
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-2">🚨 High-risk comments</h3>
            {summary.high_risk_comments.length === 0 ? (
              <p className="text-sm text-slate-500">No high-severity comments in this period.</p>
            ) : (
              <div className="space-y-2">
                {summary.high_risk_comments.map((c) => (
                  <AlertCard
                    key={c.id}
                    alert={{
                      alert_type: c.severity > 80 ? "critical" : "high_severity",
                      severity: c.severity > 80 ? "CRITICAL" : c.severity > 60 ? "HIGH" : c.severity > 30 ? "MEDIUM" : "LOW",
                      created_at: c.created_at,
                      comment: { platform: c.platform, text: c.text, comment_url: c.comment_url },
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
