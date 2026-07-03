import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar.jsx";
import { getAdminStats } from "../services/api.js";

export default function AdminDashboard() {
  const [stats, setStats] = useState({ users: 0, documents: 0, processed: 0, storage_mode: "local" });

  useEffect(() => {
    getAdminStats().then(setStats).catch(() => {});
  }, []);

  return (
    <div className="workspace-shell">
      <Sidebar />
      <section className="workspace-main">
        <p className="section-kicker">Admin</p>
        <h1 className="page-title">Usage overview</h1>
        <div className="mt-8 grid gap-4 md:grid-cols-4">
          {Object.entries(stats).map(([key, value]) => (
            <article key={key} className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-semibold capitalize text-slate-500">{key.replace("_", " ")}</p>
              <p className="mt-3 text-3xl font-extrabold text-slate-950">{value}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
