import { FileText } from "lucide-react";

export default function FileCard({ title, meta, status = "Ready" }) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-blue-50 text-brand">
          <FileText size={18} aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h3 className="truncate text-sm font-bold text-slate-950">{title}</h3>
          <p className="mt-1 text-xs text-slate-500">{meta}</p>
          <span className="mt-3 inline-flex rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
            {status}
          </span>
        </div>
      </div>
    </article>
  );
}
