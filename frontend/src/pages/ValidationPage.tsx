import { SummaryCards } from "../components/SummaryCards";
import { ValidationTable } from "../components/ValidationTable";
import type {
  AccountRecord,
  SchemaValidation,
  Summary,
} from "../types";

type Props = {
  records: AccountRecord[];
  summary: Summary;
  schemaStatus: SchemaValidation;
  busy: boolean;
  error: string;
  allowDraft: boolean;
  onAllowDraft: (value: boolean) => void;
  onRecordsChange: (records: AccountRecord[]) => void;
  onRevalidate: () => void;
  onGenerate: () => void;
  onBack: () => void;
};

export function ValidationPage({
  records,
  summary,
  schemaStatus,
  busy,
  error,
  allowDraft,
  onAllowDraft,
  onRecordsChange,
  onRevalidate,
  onGenerate,
  onBack,
}: Props) {
  const blocking = summary.errorRecords > 0;
  return (
    <section className="page-card wide">
      <div className="eyebrow">Step 3 of 4</div>
      <div className="title-row">
        <div>
          <h1>Review validation results</h1>
          <p className="page-intro">
            Correct editable fields, then revalidate before generating XML.
          </p>
        </div>
        <button className="secondary" onClick={onRevalidate} type="button">
          Revalidate changes
        </button>
      </div>
      <SummaryCards summary={summary} />

      <div className="breakdown-panel">
        <strong>Country breakdown</strong>
        <div className="country-list">
          {Object.entries(summary.countryBreakdown).map(([country, count]) => (
            <span key={country}>
              {country} <b>{count}</b>
            </span>
          ))}
        </div>
      </div>

      <div className={`alert ${schemaStatus.valid ? "success" : "warning"}`}>
        <strong>XSD status: {schemaStatus.status}</strong>
        <span>{schemaStatus.message}</span>
        {!!schemaStatus.missingImports.length && (
          <span>
            Missing: <code>{schemaStatus.missingImports.join(", ")}</code>
          </span>
        )}
      </div>

      <ValidationTable records={records} onChange={onRecordsChange} />
      {error && <div className="alert danger">{error}</div>}

      {!schemaStatus.valid && (
        <label className="draft-consent">
          <input
            checked={allowDraft}
            onChange={(event) => onAllowDraft(event.target.checked)}
            type="checkbox"
          />
          <span>
            Export a clearly marked draft even though full XSD validation
            cannot complete. This file is not submission-ready.
          </span>
        </label>
      )}
      <div className="action-row">
        <button className="secondary" onClick={onBack} type="button">
          Back to settings
        </button>
        <button
          className="primary"
          disabled={blocking || busy || (!schemaStatus.valid && !allowDraft)}
          onClick={onGenerate}
          type="button"
        >
          {busy
            ? "Generating and validating..."
            : blocking
              ? `Resolve ${summary.errorRecords} error records`
              : "Generate XML"}
        </button>
      </div>
    </section>
  );
}
