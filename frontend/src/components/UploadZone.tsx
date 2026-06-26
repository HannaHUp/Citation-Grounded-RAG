import { useRef, useState } from "react";

interface Props {
  onUpload: (file: File) => void;
  uploading: boolean;
  error: string | null;
}

const MAX_MB = 20;
const ACCEPTED = [".pdf", ".docx"];

function validateFile(file: File): string | null {
  const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
  if (!ACCEPTED.includes(ext)) {
    return "Unsupported file type. Please upload a PDF or DOCX.";
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    return "File too large. Maximum size is 20 MB.";
  }
  return null;
}

export default function UploadZone({ onUpload, uploading, error }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const displayError = localError || error;

  function handleFile(file: File) {
    const err = validateFile(file);
    if (err) { setLocalError(err); return; }
    setLocalError(null);
    onUpload(file);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  }

  const zoneClass = [
    "upload-zone",
    dragActive ? "upload-zone--drag-active" : "",
    displayError ? "upload-zone--error" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={zoneClass}
      onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        style={{ display: "none" }}
        onChange={onInputChange}
      />
      <p className="upload-zone__heading">Upload a contract or complaint</p>
      <p className="upload-zone__body">
        {uploading
          ? "Uploading…"
          : "Drag & drop a PDF or DOCX, or click to browse. Max 20 MB."}
      </p>
      {displayError && <p className="upload-zone__error">{displayError}</p>}
    </div>
  );
}
