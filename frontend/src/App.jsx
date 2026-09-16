import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Alerts from "./pages/Alerts";
import Comments from "./pages/Comments";
import Dashboard from "./pages/Dashboard";
import Platforms from "./pages/Platforms";
import Topics from "./pages/Topics";
import Trends from "./pages/Trends";
import { getHealth } from "./services/api";

function App() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    getHealth()
      .then(() => setStatus("connected"))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <div className="flex-1 min-w-0">
          <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
            <div>
              <h1 className="text-base font-semibold text-slate-800">Social Sentiment &amp; Reputation Dashboard</h1>
              <p className="text-xs text-slate-500">Packages Group</p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  status === "connected" ? "bg-green-500" : status === "unreachable" ? "bg-red-500" : "bg-yellow-400"
                }`}
              />
              Backend {status}
            </div>
          </header>
          <main className="p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/comments" element={<Comments />} />
              <Route path="/trends" element={<Trends />} />
              <Route path="/topics" element={<Topics />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/platforms" element={<Platforms />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
