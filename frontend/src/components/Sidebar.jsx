import { NavLink } from "react-router-dom";
import { BarChart3, Clock3, FilePenLine, Files, Gauge, Shield, UploadCloud } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

const items = [
  { to: "/dashboard", label: "Overview", icon: Gauge },
  { to: "/upload", label: "Upload", icon: UploadCloud },
  { to: "/batch", label: "Batch", icon: Files },
  { to: "/editor", label: "Editor", icon: FilePenLine },
  { to: "/history", label: "History", icon: Clock3 },
  { to: "/admin", label: "Admin", icon: BarChart3 },
  { to: "/pricing", label: "Plans", icon: Shield },
];

export default function Sidebar() {
  const { user } = useAuth();
  const visibleItems = items.filter((item) => item.to !== "/admin" || user?.role === "admin");

  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white px-4 py-6 lg:block">
      <div className="mb-6 rounded-md bg-slate-950 p-4 text-white">
        <p className="text-sm font-semibold">Smart Command Box</p>
        <p className="mt-2 text-xs leading-5 text-slate-300">Upload, type a task, and let the right engine handle the document.</p>
      </div>
      <nav className="space-y-1" aria-label="Workspace navigation">
        {visibleItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex min-h-11 items-center gap-3 rounded-md px-3 py-2 text-sm font-semibold transition ${
                isActive ? "bg-blue-50 text-brand" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
              }`
            }
          >
            <Icon size={18} aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
