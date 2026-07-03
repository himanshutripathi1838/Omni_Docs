import { Link, NavLink } from "react-router-dom";
import { FileText, LogIn, Rocket } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/upload", label: "Upload" },
  { to: "/history", label: "History" },
  { to: "/pricing", label: "Pricing" },
];

export default function Navbar() {
  const { user, setUser } = useAuth();
  const userInitial = user?.name?.trim()?.[0]?.toUpperCase() || user?.email?.trim()?.[0]?.toUpperCase() || "U";

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <nav className="mx-auto flex min-h-[72px] max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3 rounded-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-slate-900 text-white">
            <FileText size={21} aria-hidden="true" />
          </span>
          <span>
            <span className="block text-lg font-extrabold">OmniDocs</span>
            <span className="hidden text-xs font-medium text-slate-500 sm:block">One place for every document.</span>
          </span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-semibold transition ${
                  isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <div className="hidden items-center gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 sm:flex">
                <span className="flex h-9 w-9 items-center justify-center rounded-md bg-slate-900 text-sm font-extrabold text-white">
                  {userInitial}
                </span>
                <span className="min-w-0">
                  <span className="block max-w-36 truncate text-sm font-extrabold text-slate-950">{user.name || "User"}</span>
                  <span className="block max-w-36 truncate text-xs font-semibold text-slate-500">{user.email}</span>
                </span>
                {user.role && (
                  <span className="rounded-md bg-blue-50 px-2 py-1 text-[11px] font-extrabold uppercase text-brand">
                    {user.role}
                  </span>
                )}
              </div>
              <button className="btn-secondary" type="button" onClick={() => setUser(null)}>
                Sign out
              </button>
            </>
          ) : (
            <Link className="btn-secondary" to="/login">
              <LogIn size={17} aria-hidden="true" />
              Login
            </Link>
          )}
          <Link className="btn-primary" to="/upload">
            <Rocket size={17} aria-hidden="true" />
            Start Editing
          </Link>
        </div>
      </nav>
    </header>
  );
}
