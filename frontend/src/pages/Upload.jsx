import { useEffect, useRef, useState } from "react";
import { Crop, Download, Eraser, Image as ImageIcon, RotateCcw, RotateCw, SlidersHorizontal, Trash2, Type } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import UploadBox from "../components/UploadBox.jsx";
import CommandBox from "../components/CommandBox.jsx";
import PreviewModal from "../components/PreviewModal.jsx";
import { saveEditedImage, uploadDocument, uploadImagesToPdf } from "../services/api.js";

function getApiErrorMessage(err, fallback) {
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return fallback;
}

function isImageFile(file) {
  return file?.type?.startsWith("image/") || /\.(png|jpe?g|webp|tiff?|heic|heif)$/i.test(file?.name || "");
}

const conversionTasks = [
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
  { task: "images_to_pdf", label: "Images to PDF", command: "Convert multiple images to PDF" },
  { task: "pdf_to_zip", label: "PDF to ZIP", command: "Convert PDF to ZIP" },
  { task: "pdf_compress", label: "PDF Compress", command: "Reduce PDF size" },
  { task: "image_compress", label: "Image Compress", command: "Compress image" },
  { task: "image_crop", label: "Image Crop", command: "Crop image" },
  { task: "scanned_pdf_to_editable_text", label: "Scanned PDF Text", command: "Convert scanned PDF to editable text" },
  { task: "ocr_extract", label: "OCR Extract", command: "Run OCR" },
];

const taskUploadRules = {
  pdf_to_word: { accept: ".pdf", title: "Upload PDF", description: "Select a PDF file only. Word, PPT, and image files will not appear here." },
  pdf_to_excel: { accept: ".pdf", title: "Upload PDF", description: "Select a PDF file only." },
  pdf_to_csv: { accept: ".pdf", title: "Upload PDF", description: "Select a PDF file only." },
  pdf_to_powerpoint: { accept: ".pdf", title: "Upload PDF", description: "Select a PDF file only." },
  pdf_to_zip: { accept: ".pdf", title: "Upload PDF", description: "Select a PDF file only." },
  pdf_compress: { accept: ".pdf", title: "Upload PDF", description: "Select a PDF file only." },
  scanned_pdf_to_editable_text: { accept: ".pdf", title: "Upload scanned PDF", description: "Select a PDF file only." },
  word_to_pdf: { accept: ".doc,.docx", title: "Upload Word file", description: "Select a Word .doc/.docx file only." },
  powerpoint_to_pdf: { accept: ".ppt,.pptx", title: "Upload PowerPoint", description: "Select a PowerPoint .ppt/.pptx file only." },
  heic_to_jpg: { accept: ".heic,.heif", title: "Upload HEIC image", description: "Select a HEIC/HEIF image only." },
  heic_to_png: { accept: ".heic,.heif", title: "Upload HEIC image", description: "Select a HEIC/HEIF image only." },
  jpg_to_heic: { accept: ".jpg,.jpeg", title: "Upload JPG image", description: "Select a JPG/JPEG image only." },
  jpg_to_png: { accept: ".jpg,.jpeg", title: "Upload JPG image", description: "Select a JPG/JPEG image only." },
  png_to_heic: { accept: ".png", title: "Upload PNG image", description: "Select a PNG image only." },
  png_to_jpg: { accept: ".png", title: "Upload PNG image", description: "Select a PNG image only." },
  image_compress: { accept: ".jpg,.jpeg,.png,.webp,.tif,.tiff,.heic,.heif", title: "Upload image", description: "Select an image file only." },
  image_crop: { accept: ".jpg,.jpeg,.png,.webp,.tif,.tiff,.heic,.heif", title: "Upload image", description: "Select an image file only for cropping." },
  excel_to_csv: { accept: ".xlsx,.xls", title: "Upload Excel file", description: "Select an Excel .xlsx/.xls file only." },
  excel_to_pdf: { accept: ".xlsx,.xls", title: "Upload Excel file", description: "Select an Excel .xlsx/.xls file only." },
  csv_to_excel: { accept: ".csv", title: "Upload CSV file", description: "Select a CSV file only." },
  csv_to_pdf: { accept: ".csv", title: "Upload CSV file", description: "Select a CSV file only." },
  markdown_to_pdf: { accept: ".md,.markdown", title: "Upload Markdown file", description: "Select a Markdown .md/.markdown file only." },
  markdown_to_word: { accept: ".md,.markdown", title: "Upload Markdown file", description: "Select a Markdown .md/.markdown file only." },
  markdown_to_html: { accept: ".md,.markdown", title: "Upload Markdown file", description: "Select a Markdown .md/.markdown file only." },
  markdown_to_text: { accept: ".md,.markdown", title: "Upload Markdown file", description: "Select a Markdown .md/.markdown file only." },
  markdown_to_powerpoint: { accept: ".md,.markdown", title: "Upload Markdown file", description: "Select a Markdown .md/.markdown file only." },
};

export default function Upload() {
  const [searchParams] = useSearchParams();
  const [file, setFile] = useState(null);
  const [imageFiles, setImageFiles] = useState([]);
  const [multiImageOutputName, setMultiImageOutputName] = useState("images_combined.pdf");
  const [command, setCommand] = useState("");
  const [selectedTask, setSelectedTask] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [error, setError] = useState("");
  const [loginRequired, setLoginRequired] = useState(false);
  const [result, setResult] = useState(null);
  const [imageResult, setImageResult] = useState(null);
  const [rotation, setRotation] = useState(0);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [grayscale, setGrayscale] = useState(false);
  const [imageOutputFormat, setImageOutputFormat] = useState("pdf");
  const [imageOutputName, setImageOutputName] = useState("");
  const [targetSizeMb, setTargetSizeMb] = useState("");
  const [cropWidth, setCropWidth] = useState("");
  const [cropHeight, setCropHeight] = useState("");
  const [ocrText, setOcrText] = useState("");
  const [textEdits, setTextEdits] = useState([]);
  const [manualText, setManualText] = useState("");
  const [manualFontSize, setManualFontSize] = useState(28);
  const [manualTextColor, setManualTextColor] = useState("#111827");
  const [coverOldText, setCoverOldText] = useState(true);
  const [coverColor, setCoverColor] = useState("#ffffff");
  const [coverWidth, setCoverWidth] = useState(220);
  const [coverHeight, setCoverHeight] = useState(44);
  const [selectedTextEditId, setSelectedTextEditId] = useState("");
  const [imageToolMode, setImageToolMode] = useState("text");
  const [eraseStrokes, setEraseStrokes] = useState([]);
  const [eraserSize, setEraserSize] = useState(34);
  const [eraserColor, setEraserColor] = useState("#ffffff");
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const imageUrlRef = useRef("");
  const dragRef = useRef(null);
  const suppressNextCanvasClickRef = useRef(false);
  const hasImage = isImageFile(file);
  const isMarkdownTask = selectedTask.startsWith("markdown_");
  const selectedTaskConfig = conversionTasks.find((item) => item.task === selectedTask);
  const uploadRule = taskUploadRules[selectedTask] || {};
  const showImageEditor = hasImage && (!selectedTask || selectedTask === "ocr_extract");
  const visibleConversionTasks = selectedTask
    ? isMarkdownTask
      ? conversionTasks.filter((item) => item.task.startsWith("markdown_"))
      : conversionTasks.filter((item) => item.task === selectedTask)
    : conversionTasks;

  useEffect(() => {
    const task = searchParams.get("task");
    if (task === "pdf-to-word") {
      setCommand("Convert this PDF to Word");
      setSelectedTask("pdf_to_word");
    } else if (task === "pdf-to-excel") {
      setCommand("Convert this PDF to Excel");
      setSelectedTask("pdf_to_excel");
    } else if (task === "pdf-to-csv") {
      setCommand("Convert this PDF to CSV");
      setSelectedTask("pdf_to_csv");
    } else if (task === "word-to-pdf") {
      setCommand("Convert this Word file to PDF");
      setSelectedTask("word_to_pdf");
    } else if (task) {
      const match = conversionTasks.find((item) => item.task === task.replaceAll("-", "_"));
      if (match) {
        setCommand(match.command);
        setSelectedTask(match.task);
      }
    }
  }, [searchParams]);

  function chooseConversion(task) {
    setSelectedTask(task);
    setFile(null);
    setImageFiles([]);
    setResult(null);
    const commands = Object.fromEntries(conversionTasks.map((item) => [item.task, item.command]));
    setCommand(commands[task] || "Extract text");
  }

  function handleCommandChange(nextCommand) {
    setCommand(nextCommand);
    setSelectedTask("");
  }

  function getCanvasPoint(event) {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * canvas.width,
      y: ((event.clientY - rect.top) / rect.height) * canvas.height,
    };
  }

  function getTextEditBounds(item) {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    let textWidth = item.coverWidth;
    if (context) {
      context.save();
      context.font = `700 ${item.fontSize}px Arial, sans-serif`;
      textWidth = context.measureText(item.text).width + 16;
      context.restore();
    }
    return {
      x: item.x,
      y: item.y,
      width: item.coverOldText ? item.coverWidth : textWidth,
      height: item.coverOldText ? item.coverHeight : item.fontSize + 12,
    };
  }

  function findTextEditAtPoint(point) {
    if (!point) return null;
    return [...textEdits].reverse().find((item) => {
      const bounds = getTextEditBounds(item);
      return point.x >= bounds.x && point.x <= bounds.x + bounds.width && point.y >= bounds.y && point.y <= bounds.y + bounds.height;
    });
  }

  useEffect(() => {
    setImageResult(null);
    setLoginRequired(false);
    setRotation(0);
    setBrightness(100);
    setContrast(100);
    setGrayscale(false);
    setOcrText("");
    setTextEdits([]);
    setSelectedTextEditId("");
    setImageToolMode("text");
    setEraseStrokes([]);
    setManualText("");
    setImageOutputName(file ? `${file.name.replace(/\.[^.]+$/i, "")}-edited` : "");

    if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
    imageRef.current = null;

    if (!hasImage) return undefined;

    const image = new Image();
    const imageUrl = URL.createObjectURL(file);
    imageUrlRef.current = imageUrl;
    image.onload = () => {
      imageRef.current = image;
      drawImage();
    };
    image.src = imageUrl;

    return () => {
      if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
      imageUrlRef.current = "";
    };
  }, [file, hasImage]);

  useEffect(() => {
    if (hasImage) drawImage();
  }, [rotation, brightness, contrast, grayscale, eraseStrokes, textEdits, selectedTextEditId, hasImage]);

  useEffect(() => {
    const selected = textEdits.find((item) => item.id === selectedTextEditId);
    if (!selected) return;
    setManualText(selected.text);
    setManualFontSize(selected.fontSize);
    setManualTextColor(selected.color);
    setCoverColor(selected.coverColor);
    setCoverWidth(selected.coverWidth);
    setCoverHeight(selected.coverHeight);
    setCoverOldText(selected.coverOldText);
  }, [selectedTextEditId]);

  function drawImage() {
    const image = imageRef.current;
    const canvas = canvasRef.current;
    if (!image || !canvas) return;

    const normalizedRotation = ((rotation % 360) + 360) % 360;
    const isSideways = normalizedRotation === 90 || normalizedRotation === 270;
    canvas.width = isSideways ? image.naturalHeight : image.naturalWidth;
    canvas.height = isSideways ? image.naturalWidth : image.naturalHeight;

    const context = canvas.getContext("2d");
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.save();
    context.filter = `brightness(${brightness}%) contrast(${contrast}%)${grayscale ? " grayscale(100%)" : ""}`;
    context.translate(canvas.width / 2, canvas.height / 2);
    context.rotate((normalizedRotation * Math.PI) / 180);
    context.drawImage(image, -image.naturalWidth / 2, -image.naturalHeight / 2);
    context.restore();

    eraseStrokes.forEach((stroke) => {
      context.save();
      context.fillStyle = stroke.color;
      context.beginPath();
      context.arc(stroke.x, stroke.y, stroke.size / 2, 0, Math.PI * 2);
      context.fill();
      context.restore();
    });

    textEdits.forEach((item) => {
      context.save();
      context.font = `700 ${item.fontSize}px Arial, sans-serif`;
      context.textBaseline = "top";
      if (item.coverOldText) {
        context.fillStyle = item.coverColor;
        context.fillRect(item.x, item.y, item.coverWidth, item.coverHeight);
      }
      context.fillStyle = item.color;
      context.fillText(item.text, item.x + (item.coverOldText ? 6 : 0), item.y + (item.coverOldText ? 6 : 0));
      if (item.id === selectedTextEditId) {
        const textWidth = context.measureText(item.text).width + 16;
        context.strokeStyle = "#2563eb";
        context.lineWidth = Math.max(2, item.fontSize * 0.08);
        context.setLineDash([8, 5]);
        context.strokeRect(
          item.x,
          item.y,
          item.coverOldText ? item.coverWidth : textWidth,
          item.coverOldText ? item.coverHeight : item.fontSize + 12,
        );
      }
      context.restore();
    });
  }

  function resetImageEdits() {
    setRotation(0);
    setBrightness(100);
    setContrast(100);
    setGrayscale(false);
  }

  function setManualFontSizeAndSelected(nextSize) {
    setManualFontSize(nextSize);
    if (!selectedTextEditId) return;
    setTextEdits((items) => items.map((item) => (item.id === selectedTextEditId ? { ...item, fontSize: nextSize } : item)));
  }

  function setManualTextAndSelected(nextText) {
    setManualText(nextText);
    if (!selectedTextEditId) return;
    setTextEdits((items) => items.map((item) => (item.id === selectedTextEditId ? { ...item, text: nextText } : item)));
  }

  function setManualTextColorAndSelected(nextColor) {
    setManualTextColor(nextColor);
    if (!selectedTextEditId) return;
    setTextEdits((items) => items.map((item) => (item.id === selectedTextEditId ? { ...item, color: nextColor } : item)));
  }

  function setCoverWidthAndSelected(nextWidth) {
    setCoverWidth(nextWidth);
    if (!selectedTextEditId) return;
    setTextEdits((items) => items.map((item) => (item.id === selectedTextEditId ? { ...item, coverWidth: nextWidth } : item)));
  }

  function setCoverHeightAndSelected(nextHeight) {
    setCoverHeight(nextHeight);
    if (!selectedTextEditId) return;
    setTextEdits((items) => items.map((item) => (item.id === selectedTextEditId ? { ...item, coverHeight: nextHeight } : item)));
  }

  function setCoverColorAndSelected(nextColor) {
    setCoverColor(nextColor);
    if (!selectedTextEditId) return;
    setTextEdits((items) => items.map((item) => (item.id === selectedTextEditId ? { ...item, coverColor: nextColor } : item)));
  }

  function setCoverOldTextAndSelected(nextValue) {
    setCoverOldText(nextValue);
    if (!selectedTextEditId) return;
    setTextEdits((items) => items.map((item) => (item.id === selectedTextEditId ? { ...item, coverOldText: nextValue } : item)));
  }

  function clearManualTextEdits() {
    setTextEdits([]);
    setSelectedTextEditId("");
  }

  function clearEraseStrokes() {
    setEraseStrokes([]);
  }

  function removeTextEdit(id) {
    setTextEdits((items) => items.filter((item) => item.id !== id));
    if (selectedTextEditId === id) setSelectedTextEditId("");
  }

  function updateTextEditPosition(id, axis, value) {
    setTextEdits((items) =>
      items.map((item) => (item.id === id ? { ...item, [axis]: Number.isFinite(value) ? value : item[axis] } : item)),
    );
  }

  function nudgeTextEdit(id, deltaX, deltaY) {
    setTextEdits((items) =>
      items.map((item) => (item.id === id ? { ...item, x: Math.max(0, item.x + deltaX), y: Math.max(0, item.y + deltaY) } : item)),
    );
  }

  function handleCanvasTextClick(event) {
    if (imageToolMode === "erase") return;
    if (suppressNextCanvasClickRef.current) {
      suppressNextCanvasClickRef.current = false;
      return;
    }
    if (dragRef.current?.dragged) return;
    if (!manualText.trim()) {
      setError("Enter replacement text first, then click the image.");
      return;
    }

    const point = getCanvasPoint(event);
    if (!point) return;
    setError("");
    const id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    setTextEdits((items) => [
      ...items,
      {
        id,
        text: manualText.trim(),
        x: point.x,
        y: point.y,
        fontSize: manualFontSize,
        color: manualTextColor,
        coverOldText,
        coverColor,
        coverWidth,
        coverHeight,
      },
    ]);
    setSelectedTextEditId(id);
  }

  function handleCanvasPointerDown(event) {
    const point = getCanvasPoint(event);
    if (imageToolMode === "erase") {
      if (!point) return;
      event.preventDefault();
      setEraseStrokes((items) => [...items, { x: point.x, y: point.y, size: eraserSize, color: eraserColor }]);
      dragRef.current = { mode: "erase", dragged: true };
      event.currentTarget.setPointerCapture(event.pointerId);
      return;
    }

    const hit = findTextEditAtPoint(point);
    if (!point || !hit) return;
    event.preventDefault();
    setSelectedTextEditId(hit.id);
    suppressNextCanvasClickRef.current = true;
    dragRef.current = {
      id: hit.id,
      offsetX: point.x - hit.x,
      offsetY: point.y - hit.y,
      dragged: false,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handleCanvasPointerMove(event) {
    if (!dragRef.current) return;
    const point = getCanvasPoint(event);
    if (!point) return;
    if (dragRef.current.mode === "erase") {
      setEraseStrokes((items) => [...items, { x: point.x, y: point.y, size: eraserSize, color: eraserColor }]);
      return;
    }

    dragRef.current.dragged = true;
    setTextEdits((items) =>
      items.map((item) =>
        item.id === dragRef.current.id
          ? {
              ...item,
              x: Math.max(0, point.x - dragRef.current.offsetX),
              y: Math.max(0, point.y - dragRef.current.offsetY),
            }
          : item,
      ),
    );
  }

  function handleCanvasPointerUp(event) {
    if (!dragRef.current) return;
    const wasDragged = dragRef.current.dragged;
    dragRef.current = wasDragged ? { dragged: true } : null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    if (wasDragged) {
      window.setTimeout(() => {
        if (dragRef.current?.dragged) dragRef.current = null;
      }, 0);
    }
  }

  async function handleSubmit() {
    setError("");
    setLoginRequired(false);
    if (selectedTask === "images_to_pdf") {
      if (!imageFiles.length) {
        setError("Select images for Multiple Images to PDF.");
        return;
      }
      setLoading(true);
      try {
        const data = await uploadImagesToPdf(imageFiles, multiImageOutputName);
        setResult(data);
      } catch (err) {
        const code = err.response?.data?.detail?.code;
        setLoginRequired(["guest_edit_limit_reached", "guest_upload_limit", "guest_id_required"].includes(code));
        setError(getApiErrorMessage(err, "Images to PDF failed. Please try again."));
      } finally {
        setLoading(false);
      }
      return;
    }

    if (!file) {
      setError("Select a document first.");
      return;
    }
    setLoading(true);
    try {
      const data = await uploadDocument(file, command || "Extract text", selectedTask, {
        targetSizeMb,
        cropWidth,
        cropHeight,
      });
      setResult(data);
    } catch (err) {
      const code = err.response?.data?.detail?.code;
      setLoginRequired(["guest_edit_limit_reached", "guest_upload_limit", "guest_id_required"].includes(code));
      setError(getApiErrorMessage(err, "Processing failed. Please try again."));
    } finally {
      setLoading(false);
    }
  }

  async function handleImageExport(event) {
    event.preventDefault();
    setError("");
    setLoginRequired(false);
    setImageResult(null);

    if (!file || !hasImage) {
      setError("Select an image file.");
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) {
      setError("Image preview is not ready. Please upload the image again.");
      return;
    }

    setImageLoading(true);
    try {
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png", 0.95));
      if (!blob) throw new Error("Image export failed");
      const editedFile = new File([blob], `${file.name.replace(/\.[^.]+$/i, "")}-edited.png`, { type: "image/png" });
      const data = await saveEditedImage({
        file: editedFile,
        outputFormat: imageOutputFormat,
        outputName: imageOutputName,
        ocrText,
      });
      setImageResult(data);
    } catch (err) {
      setLoginRequired(err.response?.status === 403 && err.response?.data?.detail?.code === "guest_edit_limit_reached");
      setError(getApiErrorMessage(err, "Image edit could not be saved."));
    } finally {
      setImageLoading(false);
    }
  }

  return (
    <div className="workspace-shell">
      <Sidebar />
      <section className="workspace-main">
        <p className="section-kicker">Upload</p>
        <h1 className="page-title">Run a document workflow</h1>
        <p className="mt-3 max-w-3xl text-sm font-semibold text-slate-600">
          Guest mode: 3 free edits/processes and max 3 MB upload. After login, uploads up to 70 MB are allowed.
        </p>
        {selectedTaskConfig && (
          <div className="mt-5 flex flex-wrap items-center gap-3 rounded-md border border-blue-100 bg-blue-50 px-4 py-3">
            <span className="text-sm font-extrabold text-slate-950">Selected tool: {selectedTaskConfig.label}</span>
            <button className="btn-secondary" type="button" onClick={() => setSelectedTask("")}>
              Show all tools
            </button>
          </div>
        )}
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {visibleConversionTasks.map((item) => (
            <button
              key={item.task}
              className={selectedTask === item.task ? "segmented-active justify-center" : "btn-secondary justify-center"}
              type="button"
              onClick={() => chooseConversion(item.task)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="mt-8 grid gap-6 xl:grid-cols-[1fr_420px]">
          {selectedTask === "images_to_pdf" ? (
            <MultipleImagePicker
              files={imageFiles}
              onFilesChange={setImageFiles}
              outputName={multiImageOutputName}
              onOutputNameChange={setMultiImageOutputName}
            />
          ) : (
            <UploadBox file={file} onFileChange={setFile} accept={uploadRule.accept} title={uploadRule.title} description={uploadRule.description} />
          )}
          {selectedTask ? (
            <StartTaskPanel
              label={selectedTaskConfig?.label || "Selected tool"}
              selectedTask={selectedTask}
              targetSizeMb={targetSizeMb}
              setTargetSizeMb={setTargetSizeMb}
              cropWidth={cropWidth}
              setCropWidth={setCropWidth}
              cropHeight={cropHeight}
              setCropHeight={setCropHeight}
              onSubmit={handleSubmit}
              loading={loading}
            />
          ) : (
            <CommandBox command={command} setCommand={handleCommandChange} onSubmit={handleSubmit} loading={loading} />
          )}
        </div>
        {showImageEditor && (
          <ImageOcrEditor
            canvasRef={canvasRef}
            rotation={rotation}
            setRotation={setRotation}
            brightness={brightness}
            setBrightness={setBrightness}
            contrast={contrast}
            setContrast={setContrast}
            grayscale={grayscale}
            setGrayscale={setGrayscale}
            outputFormat={imageOutputFormat}
            setOutputFormat={setImageOutputFormat}
            outputName={imageOutputName}
            setOutputName={setImageOutputName}
            ocrText={ocrText}
            setOcrText={setOcrText}
            textEdits={textEdits}
            selectedTextEditId={selectedTextEditId}
            setSelectedTextEditId={setSelectedTextEditId}
            imageToolMode={imageToolMode}
            setImageToolMode={setImageToolMode}
            eraserSize={eraserSize}
            setEraserSize={setEraserSize}
            eraserColor={eraserColor}
            setEraserColor={setEraserColor}
            manualText={manualText}
            setManualText={setManualTextAndSelected}
            manualFontSize={manualFontSize}
            setManualFontSize={setManualFontSizeAndSelected}
            manualTextColor={manualTextColor}
            setManualTextColor={setManualTextColorAndSelected}
            coverOldText={coverOldText}
            setCoverOldText={setCoverOldTextAndSelected}
            coverColor={coverColor}
            setCoverColor={setCoverColorAndSelected}
            coverWidth={coverWidth}
            setCoverWidth={setCoverWidthAndSelected}
            coverHeight={coverHeight}
            setCoverHeight={setCoverHeightAndSelected}
            loading={imageLoading}
            onReset={resetImageEdits}
            onClearErase={clearEraseStrokes}
            onClearText={clearManualTextEdits}
            onRemoveText={removeTextEdit}
            onUpdateTextPosition={updateTextEditPosition}
            onNudgeText={nudgeTextEdit}
            onCanvasClick={handleCanvasTextClick}
            onCanvasPointerDown={handleCanvasPointerDown}
            onCanvasPointerMove={handleCanvasPointerMove}
            onCanvasPointerUp={handleCanvasPointerUp}
            onSubmit={handleImageExport}
          />
        )}
        {error && (
          <div className="form-error mt-6">
            <p>{error}</p>
            {loginRequired && (
              <Link className="mt-3 inline-flex font-extrabold text-red-800 underline" to="/login">
                Log in to continue editing
              </Link>
            )}
          </div>
        )}
        <PreviewModal result={result} onClose={() => setResult(null)} />
        <PreviewModal result={imageResult} onClose={() => setImageResult(null)} />
      </section>
    </div>
  );
}

function StartTaskPanel({
  label,
  selectedTask,
  targetSizeMb,
  setTargetSizeMb,
  cropWidth,
  setCropWidth,
  cropHeight,
  setCropHeight,
  onSubmit,
  loading,
}) {
  const isCompressTask = selectedTask === "pdf_compress" || selectedTask === "image_compress";
  const isCropTask = selectedTask === "image_crop";

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-bold text-slate-950">{label}</p>
      {isCompressTask && (
        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4">
          <label className="form-label mt-0" htmlFor="target-size-mb">Target size MB</label>
          <input
            id="target-size-mb"
            className="form-input"
            type="number"
            min="0.01"
            step="0.01"
            value={targetSizeMb}
            onChange={(event) => setTargetSizeMb(event.target.value)}
            placeholder="Example: 1.5"
          />
          <p className="mt-2 text-xs font-semibold leading-5 text-slate-600">
            Leave blank for normal compression. If the target is too small, the app will return the best possible output and show the status.
          </p>
        </div>
      )}
      {isCropTask && (
        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center gap-2">
            <Crop size={18} className="text-brand" aria-hidden="true" />
            <p className="text-sm font-extrabold text-slate-950">Crop size in pixels</p>
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <label className="form-label mt-0" htmlFor="crop-width">Width</label>
              <input
                id="crop-width"
                className="form-input"
                type="number"
                min="1"
                step="1"
                value={cropWidth}
                onChange={(event) => setCropWidth(event.target.value)}
                placeholder="Example: 800"
              />
            </div>
            <div>
              <label className="form-label mt-0" htmlFor="crop-height">Height</label>
              <input
                id="crop-height"
                className="form-input"
                type="number"
                min="1"
                step="1"
                value={cropHeight}
                onChange={(event) => setCropHeight(event.target.value)}
                placeholder="Example: 600"
              />
            </div>
          </div>
          <p className="mt-2 text-xs font-semibold leading-5 text-slate-600">
            Crop will not resize the image. It crops from the center and the output pixel size will be exactly width x height.
          </p>
        </div>
      )}
      <button className="btn-primary mt-4 w-full justify-center" type="button" onClick={onSubmit} disabled={loading}>
        <Download size={17} aria-hidden="true" />
        {loading ? "Processing..." : `Start ${label}`}
      </button>
    </section>
  );
}

function ImageOcrEditor({
  canvasRef,
  rotation,
  setRotation,
  brightness,
  setBrightness,
  contrast,
  setContrast,
  grayscale,
  setGrayscale,
  outputFormat,
  setOutputFormat,
  outputName,
  setOutputName,
  ocrText,
  setOcrText,
  textEdits,
  selectedTextEditId,
  setSelectedTextEditId,
  imageToolMode,
  setImageToolMode,
  eraserSize,
  setEraserSize,
  eraserColor,
  setEraserColor,
  manualText,
  setManualText,
  manualFontSize,
  setManualFontSize,
  manualTextColor,
  setManualTextColor,
  coverOldText,
  setCoverOldText,
  coverColor,
  setCoverColor,
  coverWidth,
  setCoverWidth,
  coverHeight,
  setCoverHeight,
  loading,
  onReset,
  onClearErase,
  onClearText,
  onRemoveText,
  onUpdateTextPosition,
  onNudgeText,
  onCanvasClick,
  onCanvasPointerDown,
  onCanvasPointerMove,
  onCanvasPointerUp,
  onSubmit,
}) {
  const selectedTextEdit = textEdits.find((item) => item.id === selectedTextEditId);

  return (
    <section className="mt-8 rounded-md border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-blue-50 text-brand">
          <ImageIcon size={22} aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">Image OCR editor</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Edit the image, adjust OCR text, then export as PDF, Word, or Image.
          </p>
        </div>
      </div>

      <form className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]" onSubmit={onSubmit}>
        <div className="rounded-md border border-slate-200 bg-slate-100 p-3">
          <div className="image-canvas-shell">
            <canvas
              ref={canvasRef}
              className="image-edit-canvas"
              aria-label="Editable image preview"
              onClick={onCanvasClick}
              onPointerDown={onCanvasPointerDown}
              onPointerMove={onCanvasPointerMove}
              onPointerUp={onCanvasPointerUp}
              onPointerCancel={onCanvasPointerUp}
            />
          </div>
          <p className="mt-2 text-center text-xs font-bold text-slate-500">
            In Text mode, click or drag to place text. In Erase mode, drag the mouse to erase old text first.
          </p>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={18} className="text-brand" aria-hidden="true" />
            <h3 className="font-extrabold text-slate-950">Edit controls</h3>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn-secondary" type="button" onClick={() => setRotation(rotation - 90)}>
              <RotateCcw size={17} aria-hidden="true" />
              Rotate left
            </button>
            <button className="btn-secondary" type="button" onClick={() => setRotation(rotation + 90)}>
              <RotateCw size={17} aria-hidden="true" />
              Rotate right
            </button>
          </div>

          <label className="form-label" htmlFor="brightness">Brightness</label>
          <input id="brightness" className="w-full accent-blue-600" type="range" min="50" max="150" value={brightness} onChange={(event) => setBrightness(Number(event.target.value))} />

          <label className="form-label" htmlFor="contrast">Contrast</label>
          <input id="contrast" className="w-full accent-blue-600" type="range" min="50" max="170" value={contrast} onChange={(event) => setContrast(Number(event.target.value))} />

          <label className="mt-5 flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 text-sm font-bold text-slate-800">
            <input type="checkbox" checked={grayscale} onChange={(event) => setGrayscale(event.target.checked)} />
            Grayscale
          </label>

          <button className="btn-secondary mt-4 w-full justify-center" type="button" onClick={onReset}>
            Reset image edits
          </button>

          <div className="mt-6 rounded-md border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <Eraser size={18} className="text-brand" aria-hidden="true" />
              <h3 className="font-extrabold text-slate-950">Erase first</h3>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2">
              <button
                className={imageToolMode === "text" ? "segmented-active justify-center" : "segmented-button justify-center border border-slate-200 bg-white"}
                type="button"
                onClick={() => setImageToolMode("text")}
              >
                Text
              </button>
              <button
                className={imageToolMode === "erase" ? "segmented-active justify-center" : "segmented-button justify-center border border-slate-200 bg-white"}
                type="button"
                onClick={() => setImageToolMode("erase")}
              >
                Erase
              </button>
            </div>

            <label className="form-label" htmlFor="eraser-size">Eraser size</label>
            <input
              id="eraser-size"
              className="w-full accent-blue-600"
              type="range"
              min="8"
              max="180"
              value={eraserSize}
              onChange={(event) => setEraserSize(Number(event.target.value))}
            />

            <label className="form-label" htmlFor="eraser-color">Eraser color</label>
            <input
              id="eraser-color"
              className="form-input h-11 p-1"
              type="color"
              value={eraserColor}
              onChange={(event) => setEraserColor(event.target.value)}
            />

            <button className="btn-secondary mt-4 w-full justify-center" type="button" onClick={onClearErase}>
              Clear eraser marks
            </button>
          </div>

          <div className="mt-6 rounded-md border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <Type size={18} className="text-brand" aria-hidden="true" />
              <h3 className="font-extrabold text-slate-950">Manual text replace</h3>
            </div>

            <label className="form-label" htmlFor="manual-image-text">Replacement text</label>
            <input
              id="manual-image-text"
              className="form-input"
              value={manualText}
              onChange={(event) => setManualText(event.target.value)}
              placeholder="Example: New name, date, amount"
            />

            <div className="mt-2 grid gap-3 sm:grid-cols-2">
              <div>
                <label className="form-label" htmlFor="manual-font-size">Text size</label>
                <input
                  id="manual-font-size"
                  className="form-input"
                  type="number"
                  min="8"
                  max="140"
                  value={manualFontSize}
                  onChange={(event) => setManualFontSize(Number(event.target.value))}
                />
              </div>
              <div>
                <label className="form-label" htmlFor="manual-text-color">Text color</label>
                <input
                  id="manual-text-color"
                  className="form-input h-11 p-1"
                  type="color"
                  value={manualTextColor}
                  onChange={(event) => setManualTextColor(event.target.value)}
                />
              </div>
            </div>

            <label className="mt-5 flex min-h-11 items-center gap-3 rounded-md border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800">
              <input type="checkbox" checked={coverOldText} onChange={(event) => setCoverOldText(event.target.checked)} />
              Cover old text before adding new text
            </label>

            {coverOldText && (
              <>
                <div className="mt-2 grid gap-3 sm:grid-cols-3">
                  <div>
                    <label className="form-label" htmlFor="cover-width">Cover width</label>
                    <input
                      id="cover-width"
                      className="form-input"
                      type="number"
                      min="20"
                      max="2000"
                      value={coverWidth}
                      onChange={(event) => setCoverWidth(Number(event.target.value))}
                    />
                  </div>
                  <div>
                    <label className="form-label" htmlFor="cover-height">Cover height</label>
                    <input
                      id="cover-height"
                      className="form-input"
                      type="number"
                      min="12"
                      max="800"
                      value={coverHeight}
                      onChange={(event) => setCoverHeight(Number(event.target.value))}
                    />
                  </div>
                  <div>
                    <label className="form-label" htmlFor="cover-color">Cover color</label>
                    <input
                      id="cover-color"
                      className="form-input h-11 p-1"
                      type="color"
                      value={coverColor}
                      onChange={(event) => setCoverColor(event.target.value)}
                    />
                  </div>
                </div>
              </>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              <button className="btn-secondary" type="button" onClick={onClearText}>
                Clear text edits
              </button>
            </div>

            {selectedTextEdit && (
              <div className="mt-4 rounded-md border border-blue-200 bg-blue-50 p-3">
                <p className="text-sm font-extrabold text-slate-950">Fix selected text position</p>
                <p className="mt-1 text-xs font-bold text-blue-800">You can drag the selected text box with the mouse.</p>
                <div className="mt-2 grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="form-label mt-0" htmlFor="selected-text-x">X position</label>
                    <input
                      id="selected-text-x"
                      className="form-input"
                      type="number"
                      min="0"
                      step="1"
                      value={Math.round(selectedTextEdit.x)}
                      onChange={(event) => onUpdateTextPosition(selectedTextEdit.id, "x", Number(event.target.value))}
                    />
                  </div>
                  <div>
                    <label className="form-label mt-0" htmlFor="selected-text-y">Y position</label>
                    <input
                      id="selected-text-y"
                      className="form-input"
                      type="number"
                      min="0"
                      step="1"
                      value={Math.round(selectedTextEdit.y)}
                      onChange={(event) => onUpdateTextPosition(selectedTextEdit.id, "y", Number(event.target.value))}
                    />
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2">
                  <span />
                  <button className="btn-secondary justify-center" type="button" onClick={() => onNudgeText(selectedTextEdit.id, 0, -5)}>
                    Up
                  </button>
                  <span />
                  <button className="btn-secondary justify-center" type="button" onClick={() => onNudgeText(selectedTextEdit.id, -5, 0)}>
                    Left
                  </button>
                  <button className="btn-secondary justify-center" type="button" onClick={() => onNudgeText(selectedTextEdit.id, 0, 5)}>
                    Down
                  </button>
                  <button className="btn-secondary justify-center" type="button" onClick={() => onNudgeText(selectedTextEdit.id, 5, 0)}>
                    Right
                  </button>
                </div>
              </div>
            )}

            {textEdits.length > 0 && (
              <div className="mt-4 space-y-2">
                {textEdits.map((item, index) => (
                  <div
                    key={item.id}
                    className={`flex items-center justify-between gap-3 rounded-md border px-3 py-2 text-sm ${
                      item.id === selectedTextEditId ? "border-blue-300 bg-blue-50" : "border-slate-200 bg-white"
                    }`}
                  >
                    <button
                      className="min-w-0 flex-1 truncate text-left font-bold text-slate-800"
                      type="button"
                      onClick={() => setSelectedTextEditId(item.id)}
                    >
                      {index + 1}. {item.text}
                    </button>
                    <button className="icon-button shrink-0" type="button" onClick={() => onRemoveText(item.id)} aria-label={`Remove text edit ${index + 1}`}>
                      <Trash2 size={16} aria-hidden="true" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <label className="form-label" htmlFor="ocr-text">OCR text</label>
          <textarea
            id="ocr-text"
            className="mt-2 min-h-32 w-full resize-y rounded-md border border-slate-300 px-4 py-3 text-sm leading-6 text-slate-950 outline-none transition focus:border-brand focus:ring-4 focus:ring-blue-100"
            value={ocrText}
            onChange={(event) => setOcrText(event.target.value)}
            placeholder="Edit OCR text here. If left blank, the backend placeholder OCR text will be used."
          />

          <p className="form-label">Output format</p>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {["pdf", "docx", "image"].map((format) => (
              <button
                key={format}
                className={outputFormat === format ? "segmented-active justify-center" : "segmented-button justify-center border border-slate-200"}
                type="button"
                onClick={() => setOutputFormat(format)}
              >
                {format === "docx" ? "Word" : format === "image" ? "Image" : "PDF"}
              </button>
            ))}
          </div>

          <label className="form-label" htmlFor="image-output-name">Output file name</label>
          <input
            id="image-output-name"
            className="form-input"
            value={outputName}
            onChange={(event) => setOutputName(event.target.value)}
            placeholder="Example: edited-scan"
          />

          <button className="btn-primary mt-5 w-full justify-center" type="submit" disabled={loading}>
            <Download size={17} aria-hidden="true" />
            {loading ? "Exporting..." : "Export edited image"}
          </button>
        </div>
      </form>
    </section>
  );
}

function MultipleImagePicker({ files, onFilesChange, outputName, onOutputNameChange }) {
  const inputRef = useRef(null);

  return (
    <section className="rounded-md border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-blue-50 text-brand">
          <ImageIcon size={22} aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">Multiple Images to PDF</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">Select JPG, PNG, WebP, TIFF, or HEIC images. PDF pages will follow the selected list order.</p>
        </div>
      </div>

      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.webp,.tif,.tiff,.heic,.heif"
        onChange={(event) => onFilesChange(Array.from(event.target.files || []))}
      />

      <button className="upload-zone mt-5 w-full border-slate-300 bg-white" type="button" onClick={() => inputRef.current?.click()}>
        <span className="block text-lg font-bold text-slate-950">Choose images</span>
        <span className="mt-2 block text-sm text-slate-600">{files.length ? `${files.length} images selected` : "Select multiple images"}</span>
      </button>

      {files.length > 0 && (
        <div className="mt-4 max-h-44 overflow-auto rounded-md border border-slate-200 bg-slate-50">
          {files.map((item, index) => (
            <p key={`${item.name}-${item.size}-${index}`} className="border-b border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 last:border-b-0">
              {index + 1}. {item.name}
            </p>
          ))}
        </div>
      )}

      <label className="form-label" htmlFor="multi-image-output-name">Output PDF name</label>
      <input
        id="multi-image-output-name"
        className="form-input"
        value={outputName}
        onChange={(event) => onOutputNameChange(event.target.value)}
        placeholder="images_combined.pdf"
      />
    </section>
  );
}
