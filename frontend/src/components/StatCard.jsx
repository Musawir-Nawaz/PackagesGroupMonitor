function StatCard({ label, value, accent }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 flex-1 min-w-[140px]">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-semibold mt-1" style={accent ? { color: accent } : undefined}>
        {value}
      </p>
    </div>
  );
}

export default StatCard;
