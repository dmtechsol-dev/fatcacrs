import { downloadUrl } from "../api/client";
import type { GenerationResult } from "../types";

type Props = {
  result: GenerationResult;
  onBack: () => void;
};

export function XmlPreviewPage({ result, onBack }: Props) {
  const artifacts = [
    ["XML file", result.xml],
    ["JSON report", result.validationJson],
    ["Text report", result.validationText],
  ] as const;

  return (
    <section className="page-card wide">
      <div className="eyebrow">Step 4 of 4</div>
      <div className="title-row">
        <div>
          <h1>{result.draft ? "Draft XML generated" : "XML ready to download"}</h1>
          <p className="page-intro">
            MessageRefId: <code>{result.messageRefId}</code>
          </p>
        </div>
        <span className={result.draft ? "result-badge draft" : "result-badge valid"}>
          {result.draft ? "UNVALIDATED DRAFT" : "XSD VALID"}
        </span>
      </div>

      <div
        className={`alert ${
          result.schemaValidation.valid ? "success" : "warning"
        }`}
      >
        <strong>{result.schemaValidation.message}</strong>
        {!!result.schemaValidation.missingImports.length && (
          <span>
            Add{" "}
            <code>{result.schemaValidation.missingImports.join(", ")}</code> to
            the backend schema directory and regenerate before submission.
          </span>
        )}
      </div>

      <div className="download-grid">
        {artifacts.map(([label, artifact]) => (
          <a
            className="download-card"
            download={artifact.fileName}
            href={downloadUrl(artifact.fileId)}
            key={label}
          >
            <span>{label}</span>
            <strong>{artifact.fileName}</strong>
            <b>Download</b>
          </a>
        ))}
      </div>

      <div className="preview-heading">
        <div>
          <span className="eyebrow">UTF-8 preview</span>
          <h2>Generated XML</h2>
        </div>
        <span>{result.xmlPreview.split("\n").length} lines</span>
      </div>
      <pre className="xml-preview">
        <code>{result.xmlPreview}</code>
      </pre>
      <div className="action-row">
        <button className="secondary" onClick={onBack} type="button">
          Return to validation
        </button>
      </div>
    </section>
  );
}
