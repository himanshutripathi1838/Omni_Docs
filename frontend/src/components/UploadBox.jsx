import { useRef, useState } from "react";
import { FileUp } from "lucide-react";

export default function UploadBox({ file, onFileChange, accept, title = "Upload your document", description }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    const nextFile = event.dataTransfer.files?.[0];
    if (nextFile) onFileChange(nextFile);
  }

  return (
    <section
      className={`upload-zone ${isDragging ? "border-brand bg-blue-50" : "border-slate-300 bg-white"}`}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        className="sr-only"
        onChange={(event) => onFileChange(event.target.files?.[0] || null)}
        accept={accept || ".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,.tif,.tiff,.heic,.heif,.xlsx,.xls,.csv,.ppt,.pptx,.txt,.md,.markdown"}
      />
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-md bg-slate-900 text-white">
        <FileUp size={24} aria-hidden="true" />
      </div>
      <h2 className="mt-5 text-xl font-bold text-slate-950">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">
        {description || "Drop PDF, Word, Image, Excel, PowerPoint, scanned files, or choose a file from your device."}
      </p>
      <button className="btn-primary mt-5" type="button" onClick={() => inputRef.current?.click()}>
        Choose file
      </button>
      {file && (
        <p className="mt-4 rounded-md bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
          Selected: {file.name}
        </p>
      )}
    </section>
  );
}
