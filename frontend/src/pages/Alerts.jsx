import { useEffect, useState } from "react";
import AlertCard from "../components/AlertCard";
import { getAlerts } from "../services/api";

function Alerts() {
  const [data, setData] = useState({ comment_alerts: [], negative_spike: null });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAlerts()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">Alerts</h2>

      {data.negative_spike && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-4">
          <p className="font-semibold text-red-800">🚨 Negative sentiment spike</p>
          <p className="text-sm text-red-700 mt-1">
            Negative mentions increased {data.negative_spike.increase_pct}% today (
            {data.negative_spike.today_count} vs. a {data.negative_spike.baseline_avg}/day average).{" "}
            {data.negative_spike.main_topic && (
              <>
                Main topic: <strong>{data.negative_spike.main_topic}</strong>.{" "}
              </>
            )}
            {data.negative_spike.main_platform && (
              <>
                Main platform: <strong>{data.negative_spike.main_platform}</strong>.
              </>
            )}
          </p>
        </div>
      )}

      {!loading && data.comment_alerts.length === 0 && !data.negative_spike && (
        <p className="text-sm text-slate-500">No active alerts. Nothing high-risk right now.</p>
      )}

      <div className="space-y-2">
        {data.comment_alerts.map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
      </div>
    </div>
  );
}

export default Alerts;
