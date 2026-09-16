import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getTopicBreakdown } from "../services/api";
import { SENTIMENT_COLORS } from "../utils/format";

const SERIES = [
  { key: "positive", label: "Positive" },
  { key: "neutral", label: "Neutral" },
  { key: "negative", label: "Negative" },
  { key: "mixed", label: "Mixed" },
];

function Topics() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTopicBreakdown()
      .then(setTopics)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">Discussion topics</h2>

      {!loading && topics.length === 0 && <p className="text-sm text-slate-500">No analyzed comments yet.</p>}

      {!loading && topics.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <ResponsiveContainer width="100%" height={Math.max(260, topics.length * 42)}>
            <BarChart data={topics} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12, fill: "#898781" }} tickLine={false} axisLine={{ stroke: "#c3c2b7" }} allowDecimals={false} />
              <YAxis type="category" dataKey="topic" width={150} tick={{ fontSize: 12, fill: "#0b0b0b" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ borderRadius: 8, borderColor: "#e1e0d9", fontSize: 13 }} cursor={{ fill: "#f9f9f7" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {SERIES.map(({ key, label }) => (
                <Bar key={key} dataKey={key} name={label} stackId="topic" fill={SENTIMENT_COLORS[key]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default Topics;
