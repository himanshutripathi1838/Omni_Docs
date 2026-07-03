import { useMemo, useRef, useState } from "react";
import { Download, Eye, FileStack, Play, RotateCcw, Trash2, UploadCloud } from "lucide-react";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import PreviewModal from "../components/PreviewModal.jsx";
import { API_BASE_URL, uploadDocument } from "../services/api.js";

const taskOptions = [
  { task: "pdf_to_word", label: "PDF to Word", command: "Convert this PDF to Word" },
  { task: "pdf_to_excel", label: "PDF to Excel", command: "Convert this PDF to Excel" },
  { task: "pdf_to_csv", label: "PDF to CSV", command: "Convert this PDF to CSV" },
  { task: "pdf_to_powerpoint", label: "PDF to PPT", command: "Convert this PDF to PowerPoint" },
  { task: "word_to_pdf", label: "Word to PDF", command: "Convert this Word file to PDF" },
  { task: "powerpoint_to_pdf", label: "PPT to PDF", command: "Convert this PowerPoint to PDF" },
  { task: "heic_to_jpg", label: "HEIC to JPG", command: "Convert HEIC to JPG" },
  { task: "jpg_to_heic", label: "JPG to HEIC", command: "Convert JPG to HEIC" },
  { task: "heic_to_png", label: "HEIC to PNG", command: "Convert HEIC to PNG" },
  { task: "png_to_heic", label: "PNG to HEIC", command: "Convert PNG to HEIC" },
  { task: "excel_to_csv", label: "Excel to CSV", command: "Convert Excel to CSV" },
  { task: "excel_to_pdf", label: "Excel to PDF", command: "Convert Excel to PDF" },
  { task: "csv_to_excel", label: "CSV to Excel", command: "Convert CSV to Excel" },
  { task: "csv_to_pdf", label: "CSV to PDF", command: "Convert CSV to PDF" },
  { task: "markdown_to_pdf", label: "Markdown to PDF", command: "Convert Markdown to PDF" },
  { task: "markdown_to_word", label: "Markdown to Word", command: "Convert Markdown to Word" },
  { task: "markdown_to_html", label: "Markdown to HTML", command: "Convert Markdown to HTML" },
  { task: "markdown_to_text", label: "Markdown to TXT", command: "Convert Markdown to TXT" },
  { task: "markdown_to_powerpoint", label: "Markdown to PPT", command: "Convert Markdown to PowerPoint" },
  { task: "jpg_to_png", label: "JPG to PNG", command: "Convert JPG to PNG" },
  { task: "png_to_jpg", label: "PNG to JPG", command: "Convert PNG to JPG" },
  { task: "pdf_to_zip", label: "PDF to ZIP", command: "Convert PDF to ZIP" },
  { task: "pdf_compress", label: "PDF Compress", command: "Reduce PDF size" },
  { task: "image_compress", label: "Image Compress", command: "Compress image" },
  { task: "scanned_pdf_to_editable_text", label: "Scanned PDF Text", command: "Convert scanned PDF to editable text" },
  { task: "ocr_extract", label: "OCR Extract", command: "Run OCR" },
  { task: "", label: "Smart command", command: "Extract text" },
];

function makeBatchItem(file, index) {
  return {
    id: `${file.name}-${file.size}-${file.lastModified}-${index}`,
    file,
    originalName: file.name,
    size: file.size,
    status: "queued",
    result: null,
    error: "",
    loginRequired: false,
  };
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function statusClass(status) {
  if (status === "completed") return "bg-emerald-50 text-emerald-700";
  if (status === "failed") return "bg-red-50 text-red-700";
  if (status === "processing") return "bg-blue-50 text-brand";
  return "bg-slate-100 text-slate-600";
}

function getApiErrorMessage(err, fallback) {
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return fallback;
}

export default function Batch() {
  const inputRef = useRef(null);
  const [items, setItems] = useState([]);
  const [selectedTask, setSelectedTask] = useState("pdf_to_csv");
  const [command, setCommand] = useState("Convert this PDF to CSV");
  const [processing, setProcessing] = useState(false);
  const [previewResult, setPreviewResult] = useState(null);

  const summary = useMemo(() => {
    return items.reduce(
      (total, item) => {
        total[item.status] = (total[item.status] || 0) + 1;
        return total;
      },
      { queued: 0, processing: 0, completed: 0, failed: 0 },
    );
  }, [items]);

  function addFiles(fileList) {
    const nextFiles = Array.from(fileList || []);
    if (!nextFiles.length) return;
    setItems((current) => [...current, ...nextFiles.map((file, index) => makeBatchItem(file, current.length + index))]);
  }

  function chooseTask(option) {
    setSelectedTask(option.task);
    setCommand(option.command);
  }

  function updateItem(id, patch) {
    setItems((current) => current.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  async function processBatch() {
    if (!items.length || processing) return;
    setProcessing(true);

    for (const item of items) {
      const latest = items.find((candidate) => candidate.id === item.id);
      if (latest?.status === "completed") continue;

      updateItem(item.id, { status: "processing", error: "", result: null, loginRequired: false });
      try {
        const result = await uploadDocument(item.file, command || "Extract text", selectedTask);
        updateItem(item.id, {
          status: "completed",
          result: {
            ...result,
            original_filename: item.originalName,
          },
        });
      } catch (err) {
        const code = err.response?.data?.detail?.code;
        updateItem(item.id, {
          status: "failed",
          error: getApiErrorMessage(err, "Processing failed"),
          loginRequired: ["guest_edit_limit_reached", "guest_upload_limit", "guest_id_required"].includes(code),
        });
      }
    }

    setProcessing(false);
  }

  function removeItem(id) {
    setItems((current) => current.filter((item) => item.id !== id));
  }

  function resetBatch() {
    if (processing) return;
    setItems([]);
    setPreviewResult(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="workspace-shell">
      <Sidebar />
      <section className="workspace-main">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <p className="section-kicker">Batch Processing</p>
            <h1 className="page-title">Process many files with one command</h1>
            <p className="mt-3 max-w-3xl text-sm font-semibold text-slate-600">
              Guest mode: 3 files/processes and max 3 MB per file. After login, max 70 MB per file is allowed.
            </p>
          </div>
          <button className="btn-secondary" type="button" onClick={resetBatch} disabled={processing}>
            <RotateCcw size={17} aria-hidden="true" />
            Reset
          </button>
        </div>

        <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <input
              ref={inputRef}
              className="sr-only"
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,.tif,.tiff,.heic,.heif,.xlsx,.xls,.csv,.ppt,.pptx,.txt,.md,.markdown"
              onChange={(event) => addFiles(event.target.files)}
            />
            <button className="upload-zone w-full border-slate-300 bg-white" type="button" onClick={() => inputRef.current?.click()}>
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-md bg-slate-900 text-white">
                <UploadCloud size={24} aria-hidden="true" />
              </span>
              <span className="mt-5 block text-xl font-bold text-slate-950">Choose multiple files</span>
              <span className="mx-auto mt-2 block max-w-xl text-sm leading-6 text-slate-600">
                Each file will be processed in its own row. The original file and output file stay locked to the same row.
              </span>
            </button>

            <div className="mt-5 grid gap-3 sm:grid-cols-4">
              <Metric label="Queued" value={summary.queued} />
              <Metric label="Processing" value={summary.processing} />
              <Metric label="Completed" value={summary.completed} />
              <Metric label="Failed" value={summary.failed} />
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <FileStack size={19} className="text-brand" aria-hidden="true" />
              <h2 className="font-extrabold text-slate-950">Batch command</h2>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {taskOptions.map((option) => (
                <button
                  key={option.label}
                  className={selectedTask === option.task ? "segmented-active justify-center" : "segmented-button justify-center border border-slate-200"}
                  type="button"
                  onClick={() => chooseTask(option)}
                  disabled={processing}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <label className="form-label" htmlFor="batch-command">Command</label>
            <textarea
              id="batch-command"
              className="mt-2 min-h-28 w-full resize-none rounded-md border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-4 focus:ring-blue-100"
              value={command}
              onChange={(event) => {
                setCommand(event.target.value);
                setSelectedTask("");
              }}
              disabled={processing}
            />
            <button className="btn-primary mt-4 w-full justify-center" type="button" onClick={processBatch} disabled={processing || !items.length}>
              <Play size={17} aria-hidden="true" />
              {processing ? "Processing..." : "Start batch"}
            </button>
          </section>
        </div>

        <section className="mt-8 rounded-md border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
            <h2 className="font-extrabold text-slate-950">Files</h2>
            <p className="text-sm font-semibold text-slate-500">{items.length} selected</p>
          </div>

          {items.length === 0 ? (
            <p className="p-5 text-sm font-semibold text-slate-500">No file is selected yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Original file</th>
                    <th className="px-4 py-3">Size</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Detected task</th>
                    <th className="px-4 py-3">Output</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => {
                    const downloadUrl = item.result?.output_file_url ? `${API_BASE_URL}${item.result.output_file_url}` : "";
                    return (
                      <tr key={item.id} className="border-t border-slate-200 align-top">
                        <td className="max-w-[280px] px-4 py-3 font-bold text-slate-900">{item.originalName}</td>
                        <td className="px-4 py-3 text-slate-600">{formatSize(item.size)}</td>
                        <td className="px-4 py-3">
                          <span className={`rounded-md px-2.5 py-1 text-xs font-extrabold ${statusClass(item.status)}`}>{item.status}</span>
                          {item.error && <p className="mt-2 max-w-sm text-xs font-semibold text-red-700">{item.error}</p>}
                          {item.loginRequired && (
                            <Link className="mt-1 inline-flex text-xs font-extrabold text-red-800 underline" to="/login">
                              Login required
                            </Link>
                          )}
                        </td>
                        <td className="px-4 py-3 font-semibold text-slate-600">{item.result?.detected_task || "-"}</td>
                        <td className="max-w-[260px] px-4 py-3 text-slate-600">{item.result?.output_filename || "-"}</td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-2">
                            {item.result && (
                              <button className="icon-button" type="button" onClick={() => setPreviewResult(item.result)} aria-label={`Preview ${item.originalName}`}>
                                <Eye size={16} aria-hidden="true" />
                              </button>
                            )}
                            {downloadUrl && (
                              <a className="icon-button" href={downloadUrl} download={item.result.output_filename} aria-label={`Download ${item.result.output_filename}`}>
                                <Download size={16} aria-hidden="true" />
                              </a>
                            )}
                            <button className="icon-button" type="button" onClick={() => removeItem(item.id)} disabled={processing} aria-label={`Remove ${item.originalName}`}>
                              <Trash2 size={16} aria-hidden="true" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <PreviewModal result={previewResult} onClose={() => setPreviewResult(null)} />
      </section>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <article className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-2xl font-extrabold text-slate-950">{value}</p>
      <p className="text-xs font-bold uppercase text-slate-500">{label}</p>
    </article>
  );
}
