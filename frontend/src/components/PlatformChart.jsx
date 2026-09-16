import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PLATFORM_COLORS, PLATFORM_LABELS } from "../utils/format";

function PlatformChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-slate-500 py-12 text-center">No platform data yet.</p>;
  }

  const chartData = data.map((d) => ({ ...d, label: PLATFORM_LABELS[d.platform] || d.platform }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 12, fill: "#898781" }} tickLine={false} axisLine={{ stroke: "#c3c2b7" }} allowDecimals={false} />
        <YAxis type="category" dataKey="label" width={80} tick={{ fontSize: 13, fill: "#0b0b0b" }} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={{ borderRadius: 8, borderColor: "#e1e0d9", fontSize: 13 }} cursor={{ fill: "#f9f9f7" }} />
        <Bar dataKey="count" name="Mentions" radius={[0, 4, 4, 0]} barSize={22}>
          {chartData.map((entry) => (
            <Cell key={entry.platform} fill={PLATFORM_COLORS[entry.platform] || "#898781"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default PlatformChart;
