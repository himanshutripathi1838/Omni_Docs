import { Link } from "react-router-dom";
import {
  ArrowRight,
  Bot,
  FileArchive,
  FileCog,
  FileDown,
  FileImage,
  FileSearch,
  FileSpreadsheet,
  FileText,
  FileUp,
  Files,
  History,
  ImageDown,
  Lock,
  MessageSquareText,
  Presentation,
  ScanText,
  Table2,
  Users,
} from "lucide-react";

const features = [
  { name: "PDF to Word", icon: FileDown, to: "/upload?task=pdf-to-word", action: "Convert PDF" },
  { name: "PDF to Excel", icon: FileSpreadsheet, to: "/upload?task=pdf-to-excel", action: "Export Excel" },
  { name: "PDF to CSV", icon: Table2, to: "/upload?task=pdf-to-csv", action: "Export CSV" },
  { name: "PDF to PowerPoint", icon: Presentation, to: "/upload?task=pdf-to-powerpoint", action: "Create PPT" },
  { name: "Word to PDF", icon: FileUp, to: "/upload?task=word-to-pdf", action: "Convert Word" },
  { name: "PowerPoint to PDF", icon: Presentation, to: "/upload?task=powerpoint-to-pdf", action: "Convert PPT" },
  { name: "HEIC to JPG", icon: ImageDown, to: "/upload?task=heic-to-jpg", action: "Convert image" },
  { name: "JPG to HEIC", icon: ImageDown, to: "/upload?task=jpg-to-heic", action: "Create HEIC" },
  { name: "HEIC to PNG", icon: ImageDown, to: "/upload?task=heic-to-png", action: "Create PNG" },
  { name: "PNG to HEIC", icon: ImageDown, to: "/upload?task=png-to-heic", action: "Create HEIC" },
  { name: "Excel to CSV", icon: FileSpreadsheet, to: "/upload?task=excel-to-csv", action: "Export CSV" },
  { name: "Excel to PDF", icon: FileSpreadsheet, to: "/upload?task=excel-to-pdf", action: "Create PDF" },
  { name: "CSV to Excel", icon: Table2, to: "/upload?task=csv-to-excel", action: "Create Excel" },
  { name: "CSV to PDF", icon: FileText, to: "/upload?task=csv-to-pdf", action: "Create PDF" },
  { name: "Markdown to PDF", icon: FileText, to: "/upload?task=markdown-to-pdf", action: "MD to PDF" },
  { name: "Markdown to Word", icon: FileText, to: "/upload?task=markdown-to-word", action: "MD to Word" },
  { name: "Markdown to HTML", icon: FileText, to: "/upload?task=markdown-to-html", action: "MD to HTML" },
  { name: "Markdown to TXT", icon: FileText, to: "/upload?task=markdown-to-text", action: "MD to TXT" },
  { name: "Markdown to PPT", icon: Presentation, to: "/upload?task=markdown-to-powerpoint", action: "MD to PPT" },
  { name: "JPG to PNG", icon: ImageDown, to: "/upload?task=jpg-to-png", action: "Create PNG" },
  { name: "PNG to JPG", icon: ImageDown, to: "/upload?task=png-to-jpg", action: "Create JPG" },
  { name: "Multiple Images to PDF", icon: FileImage, to: "/upload?task=images-to-pdf", action: "Create PDF" },
  { name: "PDF to ZIP", icon: FileArchive, to: "/upload?task=pdf-to-zip", action: "Create ZIP" },
  { name: "PDF Compress", icon: FileArchive, to: "/upload?task=pdf-compress", action: "Reduce size" },
  { name: "Image Compress", icon: FileImage, to: "/upload?task=image-compress", action: "Reduce image" },
  { name: "Image Crop", icon: FileImage, to: "/upload?task=image-crop", action: "Crop image" },
  { name: "Scanned PDF to Text", icon: FileSearch, to: "/upload?task=scanned-pdf-to-editable-text", action: "Make editable" },
  { name: "OCR Extract", icon: ScanText, to: "/upload?task=ocr-extract", action: "Extract text" },
  { name: "PDF Editor", icon: FileCog, to: "/editor?type=pdf", action: "Open PDF editor" },
  { name: "Word Editor", icon: FileCog, to: "/editor?type=word", action: "Open Word editor" },
  { name: "Image OCR", icon: ScanText, to: "/upload", action: "Upload image" },
  { name: "Smart Command Box", icon: Bot, to: "/upload", action: "Run command" },
  { name: "Batch Processing", icon: Files, to: "/batch", action: "Start batch" },
  { name: "Manual Editor", icon: FileCog, to: "/editor?type=pdf", action: "Edit manually" },
  { name: "AI Document Chat", icon: MessageSquareText, to: "/upload", action: "Try command" },
  { name: "Document History", icon: History, to: "/history", action: "View history" },
  { name: "Secure Storage", icon: Lock, to: "/dashboard", action: "Open dashboard" },
  { name: "Team Collaboration", icon: Users, to: "/pricing", action: "View plans" },
];

export default function Home() {
  return (
    <div>
      <section className="hero-band">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-20">
          <div className="flex flex-col justify-center">
            <p className="text-sm font-bold uppercase text-blue-200">OmniDocs</p>
            <h1 className="mt-4 max-w-3xl text-4xl font-extrabold text-white sm:text-5xl lg:text-6xl">Edit, convert, OCR, and manage documents with AI-powered workflows.</h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-200">One place for every document. Upload a file, type a command, and OmniDocs routes it to the right processing engine.</p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link className="btn-light" to="/upload">
                Start Editing
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <Link className="btn-ghost-dark" to="/dashboard">
                Open Dashboard
              </Link>
            </div>
          </div>
          <div className="document-workbench" aria-label="Document workflow preview">
            <div className="workbench-top">
              <span>invoice_scan.pdf</span>
              <span>OCR active</span>
            </div>
            <div className="workbench-body">
              <div className="workbench-page">
                <span className="line wide"></span>
                <span className="line"></span>
                <span className="line short"></span>
                <div className="table-grid">
                  {Array.from({ length: 12 }).map((_, index) => (
                    <span key={index}></span>
                  ))}
                </div>
              </div>
              <div className="command-preview">
                <p>Command</p>
                <strong>Convert this invoice to Excel</strong>
                <span>Detected task: ocr_extract</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {features.map(({ name, icon: Icon, to, action }) => (
            <Link
              key={name}
              to={to}
              className="group flex min-h-[112px] flex-col justify-between rounded-md border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
              aria-label={`${action}: ${name}`}
            >
              <Icon className="text-brand" size={22} aria-hidden="true" />
              <div className="mt-4">
                <h2 className="text-sm font-bold text-slate-950">{name}</h2>
                <span className="mt-2 inline-flex items-center gap-1 text-xs font-extrabold text-brand opacity-80 transition group-hover:opacity-100">
                  {action}
                  <ArrowRight size={13} aria-hidden="true" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
