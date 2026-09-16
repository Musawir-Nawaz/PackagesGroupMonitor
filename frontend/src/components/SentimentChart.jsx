import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SENTIMENT_COLORS } from "../utils/format";

const SERIES = [
  { key: "positive", label: "Positive" },
  { key: "neutral", label: "Neutral" },
  { key: "negative", label: "Negative" },
  { key: "mixed", label: "Mixed" },
];

function SentimentChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-slate-500 py-12 text-center">No trend data for this period yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#898781" }} tickLine={false} axisLine={{ stroke: "#c3c2b7" }} />
        <YAxis tick={{ fontSize: 12, fill: "#898781" }} tickLine={false} axisLine={false} allowDecimals={false} />
        <Tooltip
          contentStyle={{ borderRadius: 8, borderColor: "#e1e0d9", fontSize: 13 }}
          labelStyle={{ fontWeight: 600, color: "#0b0b0b" }}
        />
        <Legend wrapperStyle={{ fontSize: 13 }} />
        {SERIES.map(({ key, label }) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            name={label}
            stackId="1"
            stroke={SENTIMENT_COLORS[key]}
            fill={SENTIMENT_COLORS[key]}
            fillOpacity={0.25}
            strokeWidth={2}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export default SentimentChart;
