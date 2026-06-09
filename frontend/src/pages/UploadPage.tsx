import { useRef, useState } from "react";

type Props = {
  busy: boolean;
  error: string;
  onUpload: (file: File) => Promise<void>;
};

export function UploadPage({ busy, error, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);

  return (
    <section className="page-card upload-page">
      <div className="eyebrow">Step 1 of 4</div>
      <h1>Build a submission-ready FC XML file</h1>
      <p className="page-intro">
        Import the CRS reportable accounts workbook. Processing stays on this
        computer and the file is sent only to the local FastAPI service.
      </p>

      <div
        className={dragging ? "dropzone dragging" : "dropzone"}
        onClick={() => inputRef.current?.click()}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          setFile(event.dataTransfer.files[0] ?? null);
        }}
        role="button"
        tabIndex={0}
      >
        <input
          accept=".xlsx"
          hidden
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          ref={inputRef}
          type="file"
        />
        <span className="upload-mark">XLSX</span>
        <strong>{file ? file.name : "Drop the Excel workbook here"}</strong>
        <span>
          {file
            ? `${(file.size / 1024).toFixed(1)} KB selected`
            : "or click to choose a local .xlsx file"}
        </span>
      </div>

      {error && <div className="alert danger">{error}</div>}
      <div className="action-row end">
        <button
          className="primary"
          disabled={!file || busy}
          onClick={() => file && onUpload(file)}
          type="button"
        >
          {busy ? "Reading workbook..." : "Parse and validate workbook"}
        </button>
      </div>
      <div className="privacy-note">
        <strong>Local-first:</strong> no account data is uploaded to an external
        service.
      </div>
    </section>
  );
}
