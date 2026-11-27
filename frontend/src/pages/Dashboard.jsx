import { Link } from "react-router-dom";
import { ArrowRight, UploadCloud } from "lucide-react";
import Sidebar from "../components/Sidebar.jsx";

export default function Dashboard() {
  return (
    <div className="workspace-shell">
      <Sidebar />
      <section className="workspace-main">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <p className="section-kicker">Workspace</p>
            <h1 className="page-title">Document command center</h1>
          </div>
          <Link className="btn-primary" to="/upload">
            <UploadCloud size={17} aria-hidden="true" />
            Upload document
          </Link>
        </div>

        <Link className="mt-8 inline-flex items-center gap-1 text-sm font-bold text-brand" to="/history">
          View history <ArrowRight size={15} aria-hidden="true" />
        </Link>
      </section>
    </div>
  );
}
