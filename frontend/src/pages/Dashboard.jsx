import { Link } from "react-router-dom";
import { Activity, ArrowRight, CheckCircle2, Clock3, UploadCloud } from "lucide-react";
import Sidebar from "../components/Sidebar.jsx";
import FileCard from "../components/FileCard.jsx";

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

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Metric label="Files processed" value="128" icon={CheckCircle2} />
          <Metric label="In queue" value="06" icon={Clock3} />
          <Metric label="Success rate" value="98%" icon={Activity} />
        </div>

        <div className="mt-8">
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-extrabold text-slate-950">Recent files</h2>
              <Link className="inline-flex items-center gap-1 text-sm font-bold text-brand" to="/history">
                View history <ArrowRight size={15} aria-hidden="true" />
              </Link>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <FileCard title="invoice_scan.pdf" meta="OCR extract, completed 2 minutes ago" status="Completed" />
              <FileCard title="proposal.docx" meta="Text replace, completed today" status="Completed" />
              <FileCard title="receipt_photo.png" meta="Image to PDF, processing" status="Processing" />
              <FileCard title="monthly_report.pdf" meta="PDF to Word, completed yesterday" status="Completed" />
            </div>
          </section>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value, icon: Icon }) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
      <Icon size={20} className="text-brand" aria-hidden="true" />
      <p className="mt-4 text-3xl font-extrabold text-slate-950">{value}</p>
      <p className="mt-1 text-sm font-medium text-slate-500">{label}</p>
    </article>
  );
}
