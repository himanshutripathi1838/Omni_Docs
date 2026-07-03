import { useState } from "react";
import { Download, ExternalLink, FilePenLine, FileText, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import { API_BASE_URL, editPdfText, openDocumentForEdit, saveOpenDocumentEdit } from "../services/api.js";

const tools = ["PDF editor", "Word editor", "CSV editor", "Excel editor", "PowerPoint editor", "Text replacement"];
const documentTypes = [
  { id: "pdf", label: "PDF", accept: "application/pdf,.pdf", extension: "pdf" },
  { id: "word", label: "Word", accept: "application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx", extension: "docx" },
  { id: "csv", label: "CSV", accept: ".csv,text/csv", extension: "csv" },
  { id: "excel", label: "Excel", accept: ".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", extension: "xlsx" },
  { id: "powerpoint", label: "PowerPoint", accept: ".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation", extension: "pptx" },
];

function initialDocumentType(searchParams) {
  const type = searchParams.get("type");
  return documentTypes.some((item) => item.id === type) ? type : "pdf";
}

function outputFormatFor(type) {
  return documentTypes.find((item) => item.id === type)?.extension || "pdf";
}

function getApiErrorMessage(err, fallback) {
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return fallback;
}

export default function Editor() {
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState("open");
  const [documentType, setDocumentType] = useState(() => initialDocumentType(searchParams));
  const [file, setFile] = useState(null);
  const [oldText, setOldText] = useState("");
  const [newText, setNewText] = useState("");
  const [outputName, setOutputName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [loginRequired, setLoginRequired] = useState(false);
  const [result, setResult] = useState(null);
  const [openedDocument, setOpenedDocument] = useState(null);
  const [editedText, setEditedText] = useState("");
  const [wordBlocks, setWordBlocks] = useState([]);
  const [wordParagraphs, setWordParagraphs] = useState([]);
  const [outputFormat, setOutputFormat] = useState(() => outputFormatFor(initialDocumentType(searchParams)));
  const previewUrl = result?.preview_file_url ? `${API_BASE_URL}${result.preview_file_url}` : "";
  const downloadUrl = result?.output_file_url ? `${API_BASE_URL}${result.output_file_url}` : "";
  const canPreview = result?.output_filename?.toLowerCase().endsWith(".pdf");

  function resetResult() {
    setError("");
    setLoginRequired(false);
    setResult(null);
  }

  function changeDocumentType(nextType) {
    setDocumentType(nextType);
    setOutputFormat(outputFormatFor(nextType));
    setFile(null);
    setOpenedDocument(null);
    setEditedText("");
    setWordBlocks([]);
    setWordParagraphs([]);
    setOutputName("");
    resetResult();
  }

  function isExpectedFile(selectedFile, expectedType) {
    const name = selectedFile?.name?.toLowerCase() || "";
    if (expectedType === "pdf") return name.endsWith(".pdf");
    if (expectedType === "word") return name.endsWith(".docx");
    if (expectedType === "csv") return name.endsWith(".csv");
    if (expectedType === "excel") return name.endsWith(".xlsx") || name.endsWith(".xls");
    if (expectedType === "powerpoint") return name.endsWith(".pptx");
    return false;
  }

  async function handleOpenDocument(event) {
    event.preventDefault();
    resetResult();

    if (!file) {
      setError(`Select a ${documentTypes.find((item) => item.id === documentType)?.label || "Document"} file.`);
      return;
    }
    if (!isExpectedFile(file, documentType)) {
      setError(`Wrong file type uploaded for the ${documentTypes.find((item) => item.id === documentType)?.label || "Document"} editor.`);
      return;
    }

    setLoading(true);
    try {
      const data = await openDocumentForEdit(file, documentType);
      setOpenedDocument(data);
      setEditedText(data.text);
      setWordBlocks(data.blocks || []);
      setWordParagraphs(data.paragraphs || []);
      setOutputName(`${file.name.replace(/\.(pdf|docx|doc|csv|xlsx|xls|pptx|ppt)$/i, "")}-edited`);
      setOutputFormat(outputFormatFor(data.detected_file_type));
    } catch (err) {
      setError(err.response?.data?.detail || "Document could not be opened. Try a searchable PDF or DOCX file.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveOpenedDocument(event) {
    event.preventDefault();
    resetResult();

    if (!openedDocument) {
      setError("Open a document first.");
      return;
    }

    setLoading(true);
    try {
      const data = await saveOpenDocumentEdit({
        originalFilename: openedDocument.original_filename,
        storedFilename: openedDocument.stored_filename,
        detectedFileType: openedDocument.detected_file_type,
        editedText,
        editedBlocks: wordBlocks,
        editedParagraphs: wordParagraphs,
        outputName,
        outputFormat,
      });
      setResult(data);
    } catch (err) {
      setLoginRequired(err.response?.status === 403 && err.response?.data?.detail?.code === "guest_edit_limit_reached");
      setError(getApiErrorMessage(err, "Document could not be saved."));
    } finally {
      setLoading(false);
    }
  }

  async function handlePdfReplace(event) {
    event.preventDefault();
    resetResult();

    if (!file) {
      setError("Select a PDF file.");
      return;
    }
    if (!oldText.trim() || !newText.trim()) {
      setError("Both old text and new text are required.");
      return;
    }

    setLoading(true);
    try {
      const data = await editPdfText(file, oldText, newText, outputName);
      setResult(data);
    } catch (err) {
      setLoginRequired(err.response?.status === 403 && err.response?.data?.detail?.code === "guest_edit_limit_reached");
      setError(getApiErrorMessage(err, "PDF edit failed. Try a PDF with searchable text."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="workspace-shell">
      <Sidebar />
      <section className="workspace-main">
        <p className="section-kicker">Editor</p>
        <h1 className="page-title">Manual document editor</h1>

        <div className="mt-6 inline-flex rounded-md border border-slate-200 bg-white p-1 shadow-sm">
          <button className={mode === "open" ? "segmented-active" : "segmented-button"} type="button" onClick={() => setMode("open")}>
            <FileText size={17} aria-hidden="true" />
            Open & edit
          </button>
          <button
            className={mode === "replace" ? "segmented-active" : "segmented-button"}
            type="button"
            onClick={() => {
              setMode("replace");
              changeDocumentType("pdf");
            }}
          >
            <Search size={17} aria-hidden="true" />
            Find & replace
          </button>
        </div>

        <div className="mt-8 grid gap-6 xl:grid-cols-[1fr_360px]">
          <section className="rounded-md border border-slate-200 bg-white p-6 shadow-sm">
            {mode === "open" ? (
              <OpenEditorForm
                file={file}
                setFile={setFile}
                documentType={documentType}
                setDocumentType={changeDocumentType}
                openedDocument={openedDocument}
                editedText={editedText}
                setEditedText={setEditedText}
                wordBlocks={wordBlocks}
                setWordBlocks={setWordBlocks}
                wordParagraphs={wordParagraphs}
                setWordParagraphs={setWordParagraphs}
                outputName={outputName}
                setOutputName={setOutputName}
                outputFormat={outputFormat}
                loading={loading}
                onOpen={handleOpenDocument}
                onSave={handleSaveOpenedDocument}
              />
            ) : (
              <ReplaceForm
                file={file}
                setFile={setFile}
                oldText={oldText}
                setOldText={setOldText}
                newText={newText}
                setNewText={setNewText}
                outputName={outputName}
                setOutputName={setOutputName}
                loading={loading}
                onSubmit={handlePdfReplace}
              />
            )}

            {error && (
              <div className="form-error mt-5">
                <p>{error}</p>
                {loginRequired && (
                  <Link className="mt-3 inline-flex font-extrabold text-red-800 underline" to="/login">
                    Log in to continue editing
                  </Link>
                )}
              </div>
            )}
            {result && (
              <div className="mt-5 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                <p className="font-bold">{result.message}</p>
                <p className="mt-1 text-sm text-emerald-700">File name: {result.output_filename}</p>
                {result.is_guest && (
                  <p className="mt-1 text-sm font-bold text-emerald-700">
                    Guest edits left: {result.guest_edit_remaining} of {result.guest_edit_limit}
                  </p>
                )}
                {canPreview && (
                  <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
                    <div className="mb-3 flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                      <h3 className="font-extrabold text-slate-950">Document preview</h3>
                      <a className="btn-secondary w-full justify-center sm:w-auto" href={previewUrl} target="_blank" rel="noreferrer">
                        <ExternalLink size={17} aria-hidden="true" />
                        Open file
                      </a>
                    </div>
                    <iframe className="pdf-preview-frame" src={previewUrl} title={`Preview of ${result.output_filename}`} />
                  </div>
                )}
                <a className="btn-primary mt-4 w-full justify-center sm:w-auto" href={downloadUrl} download={result.output_filename}>
                  <Download size={17} aria-hidden="true" />
                  Download file
                </a>
              </div>
            )}
          </section>

          <aside className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-extrabold text-slate-950">Available tools</h2>
            <div className="mt-4 grid gap-3">
              {tools.map((tool) => (
                <div key={tool} className="rounded-md bg-slate-50 p-3">
                  <p className="text-sm font-bold text-slate-900">{tool}</p>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}

function OpenEditorForm({
  file,
  setFile,
  documentType,
  setDocumentType,
  openedDocument,
  editedText,
  setEditedText,
  wordBlocks,
  setWordBlocks,
  wordParagraphs,
  setWordParagraphs,
  outputName,
  setOutputName,
  outputFormat,
  loading,
  onOpen,
  onSave,
}) {
  const editorBlocks = wordBlocks.length
    ? wordBlocks
    : wordParagraphs.map((paragraph) => ({ ...paragraph, type: "paragraph", runs: [] }));
  const sourcePreviewUrl = openedDocument?.source_preview_file_url ? `${API_BASE_URL}${openedDocument.source_preview_file_url}` : "";

  function updateWordBlockText(index, nextText) {
    setWordBlocks((items) => items.map((item, itemIndex) => (itemIndex === index ? { ...item, text: nextText } : item)));
    setWordParagraphs((items) => items.map((item, itemIndex) => (itemIndex === index ? { ...item, text: nextText } : item)));
  }

  function updateWordTableCell(blockIndex, rowIndex, cellIndex, nextText) {
    setWordBlocks((items) =>
      items.map((block, itemIndex) => {
        if (itemIndex !== blockIndex || block.type !== "table") return block;
        return {
          ...block,
          rows: block.rows.map((row, currentRowIndex) =>
            currentRowIndex === rowIndex
              ? row.map((cell, currentCellIndex) => (currentCellIndex === cellIndex ? { ...cell, text: nextText } : cell))
              : row,
          ),
        };
      }),
    );
  }

  function updatePowerPointShape(slideIndex, shapeIndex, nextText) {
    setWordBlocks((items) =>
      items.map((slide, currentSlideIndex) =>
        currentSlideIndex === slideIndex
          ? {
              ...slide,
              shapes: (slide.shapes || []).map((shape, currentShapeIndex) =>
                currentShapeIndex === shapeIndex ? { ...shape, text: nextText } : shape,
              ),
            }
          : slide,
      ),
    );
  }

  const currentType = documentTypes.find((item) => item.id === documentType) || documentTypes[0];
  const openedTypeLabel = documentTypes.find((item) => item.id === openedDocument?.detected_file_type)?.label || openedDocument?.detected_file_type;

  return (
    <div>
      <div className="flex items-start gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-blue-50 text-brand">
          <FilePenLine size={22} aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">Open and edit {currentType.label} manually</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Open a file without a command, edit the text, then save the output in the same format.
          </p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2 rounded-md border border-slate-200 bg-slate-50 p-2">
        {documentTypes.map((type) => (
          <button key={type.id} className={documentType === type.id ? "segmented-active" : "segmented-button"} type="button" onClick={() => setDocumentType(type.id)}>
            {type.label}
          </button>
        ))}
      </div>

      <form className="mt-6" onSubmit={onOpen}>
        <label className="form-label" htmlFor="open-file">{currentType.label} file</label>
        <input
          key={documentType}
          id="open-file"
          className="form-input py-2"
          type="file"
          accept={currentType.accept}
          onChange={(event) => setFile(event.target.files?.[0] || null)}
        />
        {file && (
          <p className="mt-2 text-sm font-semibold text-slate-600">
            Selected: {file.name}
          </p>
        )}
        <button className="btn-secondary mt-4 w-full justify-center sm:w-auto" type="submit" disabled={loading}>
          {loading ? "Opening..." : "Open document"}
        </button>
      </form>

      {openedDocument && (
        <form className="mt-6 border-t border-slate-200 pt-6" onSubmit={onSave}>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-bold text-slate-950">{openedDocument.original_filename}</p>
              <p className="text-xs font-semibold uppercase text-slate-500">{openedTypeLabel}</p>
            </div>
            <span className="rounded-md bg-blue-50 px-3 py-2 text-sm font-extrabold text-brand">
              Save as .{outputFormat}
            </span>
          </div>

          {openedDocument.detected_file_type === "word" ? (
            <section className="mt-5">
              <label className="form-label" htmlFor="word-page-editor">Word document editor</label>
              <div id="word-page-editor" className="word-page-editor" aria-label="Word document editable preview">
                {editorBlocks.map((block, index) =>
                  block.type === "table" ? (
                    <WordTable key={block.id ?? index} block={block} blockIndex={index} onCellBlur={updateWordTableCell} />
                  ) : (
                    <WordParagraph key={block.id ?? index} block={block} blockIndex={index} onBlur={updateWordBlockText} />
                  ),
                )}
              </div>
            </section>
          ) : ["csv", "excel"].includes(openedDocument.detected_file_type) ? (
            <section className="mt-5">
              <label className="form-label" htmlFor="table-editor">Table editor</label>
              <div id="table-editor" className="word-page-editor" aria-label="Table editable preview">
                {editorBlocks.map((block, index) => (
                  <WordTable key={block.id ?? index} block={block} blockIndex={index} onCellBlur={updateWordTableCell} />
                ))}
              </div>
            </section>
          ) : openedDocument.detected_file_type === "powerpoint" ? (
            <section className="mt-5">
              <label className="form-label" htmlFor="powerpoint-editor">PowerPoint text editor</label>
              <div id="powerpoint-editor" className="space-y-4" aria-label="PowerPoint editable text">
                {wordBlocks.map((slide, slideIndex) => (
                  <div key={slide.id ?? slideIndex} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-extrabold text-slate-950">{slide.title || `Slide ${slideIndex + 1}`}</p>
                    <div className="mt-3 grid gap-3">
                      {(slide.shapes || []).map((shape, shapeIndex) => (
                        <textarea
                          key={`${slideIndex}-${shape.id ?? shapeIndex}`}
                          className="min-h-20 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-brand focus:ring-4 focus:ring-blue-100"
                          value={shape.text}
                          onChange={(event) => updatePowerPointShape(slideIndex, shapeIndex, event.target.value)}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ) : (
            <section className="pdf-edit-grid mt-5">
              <div>
                <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                  <label className="form-label mt-0" htmlFor="document-text">PDF text to edit</label>
                  {sourcePreviewUrl && (
                    <a className="btn-secondary w-full justify-center sm:w-auto" href={sourcePreviewUrl} target="_blank" rel="noreferrer">
                      <ExternalLink size={17} aria-hidden="true" />
                      Open original
                    </a>
                  )}
                </div>
                <textarea
                  id="document-text"
                  className="mt-2 min-h-[520px] w-full resize-y rounded-md border border-slate-300 px-4 py-3 font-mono text-sm leading-6 text-slate-950 outline-none transition focus:border-brand focus:ring-4 focus:ring-blue-100"
                  value={editedText}
                  onChange={(event) => setEditedText(event.target.value)}
                />
              </div>
              {sourcePreviewUrl && (
                <div>
                  <p className="form-label mt-0">Original PDF preview</p>
                  <iframe className="pdf-source-preview-frame" src={sourcePreviewUrl} title={`Original preview of ${openedDocument.original_filename}`} />
                </div>
              )}
            </section>
          )}

          <label className="form-label" htmlFor="manual-output-name">Output file name</label>
          <input
            id="manual-output-name"
            className="form-input"
            value={outputName}
            onChange={(event) => setOutputName(event.target.value)}
            placeholder={outputFormat === "pdf" ? "Example: edited-document.pdf" : "Example: edited-document.docx"}
          />

          <button className="btn-primary mt-5 w-full justify-center sm:w-auto" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save edited document"}
          </button>
        </form>
      )}
    </div>
  );
}

function WordParagraph({ block, blockIndex, onBlur }) {
  const isHeading = block.style?.toLowerCase().includes("heading");
  return (
    <p
      className={isHeading ? "word-heading" : "word-paragraph"}
      contentEditable
      suppressContentEditableWarning
      onBlur={(event) => onBlur(blockIndex, event.currentTarget.innerText)}
    >
      <WordRuns runs={block.runs} text={block.text} />
    </p>
  );
}

function WordTable({ block, blockIndex, onCellBlur }) {
  function cellStyle(cell) {
    return {
      color: cell.style?.fontColor || undefined,
      backgroundColor: cell.style?.backgroundColor || undefined,
      fontWeight: cell.style?.bold ? 700 : undefined,
      fontStyle: cell.style?.italic ? "italic" : undefined,
      textAlign: cell.style?.horizontal || undefined,
    };
  }

  return (
    <div className="word-table-wrap">
      <table className="word-table">
        <tbody>
          {(block.rows || []).map((row, rowIndex) => (
            <tr key={`${blockIndex}-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <td key={`${blockIndex}-${rowIndex}-${cellIndex}`}>
                  <div
                    className="word-cell-editor"
                    style={cellStyle(cell)}
                    contentEditable
                    suppressContentEditableWarning
                    onBlur={(event) => onCellBlur(blockIndex, rowIndex, cellIndex, event.currentTarget.innerText)}
                  >
                    <WordRuns runs={cell.runs} text={cell.text} />
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WordRuns({ runs = [], text = "" }) {
  const runText = runs.map((run) => run.text).join("");
  if (!runs.length || runText !== text) {
    return text || "\u00a0";
  }

  return runs.map((run, index) => (
    <span
      key={`${index}-${run.text}`}
      style={{
        color: run.color || undefined,
        fontWeight: run.bold ? 700 : undefined,
        fontStyle: run.italic ? "italic" : undefined,
        textDecoration: run.underline ? "underline" : undefined,
      }}
    >
      {run.text}
    </span>
  ));
}

function ReplaceForm({ file, setFile, oldText, setOldText, newText, setNewText, outputName, setOutputName, loading, onSubmit }) {
  return (
    <form onSubmit={onSubmit}>
      <div className="flex items-start gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-blue-50 text-brand">
          <Search size={22} aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">Find and replace inside a PDF</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Replace exact text and preserve the original PDF visual format as closely as possible.
          </p>
        </div>
      </div>

      <label className="form-label" htmlFor="pdf-file">PDF file</label>
      <input
        id="pdf-file"
        className="form-input py-2"
        type="file"
        accept="application/pdf,.pdf"
        onChange={(event) => setFile(event.target.files?.[0] || null)}
      />

      <label className="form-label" htmlFor="output-name">Edited PDF name</label>
      <input
        id="output-name"
        className="form-input"
        value={outputName}
        onChange={(event) => setOutputName(event.target.value)}
        placeholder="Example: updated-invoice.pdf"
      />

      <div className="mt-2 grid gap-4 md:grid-cols-2">
        <div>
          <label className="form-label" htmlFor="old-text">Old text</label>
          <input id="old-text" className="form-input" value={oldText} onChange={(event) => setOldText(event.target.value)} placeholder="Example: 9876543210" />
        </div>
        <div>
          <label className="form-label" htmlFor="new-text">New text</label>
          <input id="new-text" className="form-input" value={newText} onChange={(event) => setNewText(event.target.value)} placeholder="Example: 9123456780" />
        </div>
      </div>

      <button className="btn-primary mt-6 w-full justify-center sm:w-auto" type="submit" disabled={loading}>
        {loading ? "Editing PDF..." : "Edit PDF"}
      </button>
    </form>
  );
}
