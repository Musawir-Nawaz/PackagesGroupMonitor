import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/comments", label: "Comments" },
  { to: "/trends", label: "Trends" },
  { to: "/topics", label: "Topics" },
  { to: "/alerts", label: "Alerts" },
  { to: "/platforms", label: "Platforms" },
];

function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-slate-900 text-slate-200 min-h-screen flex flex-col">
      <div className="px-5 py-5 border-b border-slate-800">
        <h1 className="text-base font-semibold text-white leading-tight">Packages Group</h1>
        <p className="text-xs text-slate-400 mt-0.5">Reputation Monitor</p>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {LINKS.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive ? "bg-slate-700 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
