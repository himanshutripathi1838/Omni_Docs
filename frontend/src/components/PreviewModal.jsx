import { useEffect, useState } from "react";
import { Download, X } from "lucide-react";
import { API_BASE_URL, getTablePreview } from "../services/api.js";

function formatSize(bytes) {
  if (!Number.isFinite(Number(bytes))) return "-";
  const value = Number(bytes);
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function splitFileName(filename = "") {
  const dotIndex = filename.lastIndexOf(".");
  if (dotIndex <= 0) return { baseName: filename || "omnidocs-output", extension: "" };
  return {
    baseName: filename.slice(0, dotIndex),
    extension: filename.slice(dotIndex),
  };
}

export default function PreviewModal({ result, onClose }) {
  const [tablePreview, setTablePreview] = useState(null);
  const [tablePreviewError, setTablePreviewError] = useState("");
  const [textPreview, setTextPreview] = useState("");
  const [textPreviewError, setTextPreviewError] = useState("");
  const [downloadBaseName, setDownloadBaseName] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let active = true;
    setTablePreview(null);
    setTablePreviewError("");
    setTextPreview("");
    setTextPreviewError("");
    setDownloadError("");

    const filename = result?.output_filename;
    if (!filename) return undefined;
    setDownloadBaseName(splitFileName(result.original_filename || filename).baseName);

    if (/\.(txt)$/i.test(filename) && result?.preview_file_url) {
      fetch(`${API_BASE_URL}${result.preview_file_url}`)
        .then((response) => response.text())
        .then((text) => {
          if (active) setTextPreview(text);
        })
        .catch(() => {
          if (active) setTextPreviewError("Text preview could not be loaded. The download file is available.");
        });
    }

    if (!/\.(csv|xlsx)$/i.test(filename)) {
      return () => {
        active = false;
      };
    }

    getTablePreview(filename)
      .then((data) => {
        if (active) setTablePreview(data);
      })
      .catch(() => {
        if (active) setTablePreviewError("Preview could not be loaded. The download file is available.");
      });

    return () => {
      active = false;
    };
  }, [result]);

  if (!result) return null;
  const downloadUrl = result.output_file_url ? `${API_BASE_URL}${result.output_file_url}` : null;
  const previewUrl = result.preview_file_url ? `${API_BASE_URL}${result.preview_file_url}` : downloadUrl;
  const isPdfOutput = result.output_filename?.toLowerCase().endsWith(".pdf") || result.output_file_url?.toLowerCase().endsWith(".pdf");
  const isImageOutput = /\.(png|jpe?g|webp)$/i.test(result.output_filename || result.output_file_url || "");
  const isTableOutput = /\.(csv|xlsx)$/i.test(result.output_filename || result.output_file_url || "");
  const isHtmlOutput = /\.html$/i.test(result.output_filename || result.output_file_url || "");
  const isTextOutput = /\.txt$/i.test(result.output_filename || result.output_file_url || "");
  const outputExtension = splitFileName(result.output_filename).extension;

  function normalizedDownloadName() {
    const safeBaseName = downloadBaseName.trim().replace(/[\\/:*?"<>|]+/g, "-") || splitFileName(result.output_filename).baseName;
    return `${safeBaseName}${outputExtension}`;
  }

  async function handleDownload() {
    if (!downloadUrl) return;
    setDownloadError("");
    setDownloading(true);
    try {
      const response = await fetch(downloadUrl);
      if (!response.ok) throw new Error(`Download failed (${response.status})`);
      const blob = await response.blob();
      if (!blob.size) throw new Error("The output file is empty.");
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = normalizedDownloadName();
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
    } catch (err) {
      setDownloadError(`${err.message || "Download failed."} Please try converting the file again.`);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 px-4" role="dialog" aria-modal="true">
      <div className="max-h-[92dvh] w-full max-w-5xl overflow-y-auto rounded-md bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-brand">Processing complete</p>
            <h2 className="mt-1 text-2xl font-extrabold text-slate-950">{result.original_filename}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close preview">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        <dl className="mt-6 grid gap-3 rounded-md bg-slate-50 p-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="font-semibold text-slate-500">File type</dt>
            <dd className="mt-1 font-bold text-slate-950">{result.detected_file_type}</dd>
          </div>
          <div>
            <dt className="font-semibold text-slate-500">Task</dt>
            <dd className="mt-1 font-bold text-slate-950">{result.detected_task}</dd>
          </div>
          <div>
            <dt className="font-semibold text-slate-500">Original size</dt>
            <dd className="mt-1 font-bold text-slate-950">{formatSize(result.original_size)}</dd>
          </div>
          <div>
            <dt className="font-semibold text-slate-500">Output size</dt>
            <dd className="mt-1 font-bold text-slate-950">{formatSize(result.output_size)}</dd>
          </div>
          {result.reduction_percent !== null && result.reduction_percent !== undefined && (
            <div>
              <dt className="font-semibold text-slate-500">Reduction</dt>
              <dd className="mt-1 font-bold text-slate-950">{result.reduction_percent}%</dd>
            </div>
          )}
          {result.target_size && (
            <div>
              <dt className="font-semibold text-slate-500">Target size</dt>
              <dd className="mt-1 font-bold text-slate-950">{formatSize(result.target_size)}</dd>
            </div>
          )}
          {result.target_size && (
            <div>
              <dt className="font-semibold text-slate-500">Target status</dt>
              <dd className="mt-1 font-bold text-slate-950">{result.target_achieved ? "Achieved" : "Best possible"}</dd>
            </div>
          )}
        </dl>
        <p className="mt-4 text-sm leading-6 text-slate-600">{result.message}</p>
        {result.warning && <p className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900" role="status">{result.warning}</p>}
        {downloadUrl && isPdfOutput && (
          <section className="mt-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-sm font-extrabold text-slate-950">PDF preview</h3>
              <span className="rounded-md bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand">Review before download</span>
            </div>
            <iframe className="pdf-preview-frame" src={previewUrl} title={`Preview of ${result.output_filename || result.original_filename}`} />
          </section>
        )}
        {downloadUrl && isImageOutput && (
          <section className="mt-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-sm font-extrabold text-slate-950">Image preview</h3>
              <span className="rounded-md bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand">Review before download</span>
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-100 p-3">
              <img className="max-h-[560px] w-full object-contain" src={previewUrl} alt={`Preview of ${result.output_filename || result.original_filename}`} />
            </div>
          </section>
        )}
        {downloadUrl && isTableOutput && (
          <section className="mt-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-sm font-extrabold text-slate-950">Table preview</h3>
              <span className="rounded-md bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand">Review before download</span>
            </div>
            <div className="max-h-[460px] overflow-auto rounded-md border border-slate-200 bg-white">
              {tablePreview?.rows?.length ? (
                <table className="min-w-full border-collapse text-left text-sm">
                  <tbody>
                    {tablePreview.rows.map((row, rowIndex) => (
                      <tr key={`${rowIndex}-${row.join("|")}`} className={rowIndex === 0 ? "bg-slate-100" : "odd:bg-white even:bg-slate-50"}>
                        {row.map((cell, cellIndex) => (
                          <td key={`${rowIndex}-${cellIndex}`} className="max-w-[260px] whitespace-pre-wrap border border-slate-200 px-3 py-2 align-top text-slate-800">
                            {cell || "\u00a0"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="p-4 text-sm font-semibold text-slate-600">
                  {tablePreviewError || "Preview loading..."}
                </p>
              )}
            </div>
            {tablePreview?.truncated && (
              <p className="mt-2 text-xs font-semibold text-slate-500">
                Showing first {tablePreview.rows.length} rows of {tablePreview.row_count}. Download the full file for all rows.
              </p>
            )}
          </section>
        )}
        {downloadUrl && isHtmlOutput && (
          <section className="mt-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-sm font-extrabold text-slate-950">HTML preview</h3>
              <span className="rounded-md bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand">Review before download</span>
            </div>
            <iframe className="pdf-preview-frame" src={previewUrl} title={`Preview of ${result.output_filename || result.original_filename}`} />
          </section>
        )}
        {downloadUrl && isTextOutput && (
          <section className="mt-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-sm font-extrabold text-slate-950">Text preview</h3>
              <span className="rounded-md bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand">Review before download</span>
            </div>
            <pre className="max-h-[460px] overflow-auto rounded-md border border-slate-200 bg-slate-950 p-4 text-sm leading-6 text-slate-100">
              {textPreview || textPreviewError || "Preview loading..."}
            </pre>
          </section>
        )}
        {downloadUrl && (
          <div className="mt-6 rounded-md border border-slate-200 bg-slate-50 p-4">
            <label className="form-label mt-0" htmlFor="download-name">Download file name</label>
            <div className="mt-2 flex min-h-11 overflow-hidden rounded-md border border-slate-300 bg-white focus-within:border-brand focus-within:ring-4 focus-within:ring-blue-100">
              <input
                id="download-name"
                className="min-w-0 flex-1 px-4 py-3 text-sm text-slate-950 outline-none"
                value={downloadBaseName}
                onChange={(event) => setDownloadBaseName(event.target.value)}
                placeholder={splitFileName(result.output_filename).baseName}
              />
              {outputExtension && (
                <span className="flex items-center border-l border-slate-200 bg-slate-100 px-3 text-sm font-extrabold text-slate-700">
                  {outputExtension}
                </span>
              )}
            </div>
            <p className="mt-2 text-xs font-semibold text-slate-500">The extension is locked. You can only change the file name.</p>
            {downloadError && <p className="form-error mt-3" role="alert">{downloadError}</p>}
            <button className="btn-primary mt-4 w-full justify-center" type="button" onClick={handleDownload} disabled={downloading}>
            <Download size={17} aria-hidden="true" />
              {downloading ? "Downloading..." : "Download output"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
