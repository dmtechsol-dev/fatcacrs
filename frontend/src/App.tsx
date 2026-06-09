import { useState } from "react";
import {
  ApiError,
  generateXml,
  uploadExcel,
  validateRecords,
} from "./api/client";
import { SettingsPage } from "./pages/SettingsPage";
import { UploadPage } from "./pages/UploadPage";
import { ValidationPage } from "./pages/ValidationPage";
import { XmlPreviewPage } from "./pages/XmlPreviewPage";
import type {
  AccountRecord,
  GenerationResult,
  SchemaValidation,
  Settings,
  Summary,
} from "./types";

type Step = "upload" | "settings" | "validation" | "preview";

const emptySummary: Summary = {
  totalRecords: 0,
  validRecords: 0,
  errorRecords: 0,
  warningRecords: 0,
  countryBreakdown: {},
  closedAccounts: 0,
  openAccounts: 0,
  missingTin: 0,
  missingDob: 0,
  missingBalance: 0,
};

const initialSchema: SchemaValidation = {
  status: "incomplete",
  valid: false,
  fullValidation: false,
  message: "Schema readiness will be checked after upload.",
  errors: [],
  missingImports: [],
};

const initialSettings: Settings = {
  sendingCompanyIn: "",
  reportingFiTin: "",
  reportingFiTinIssuedBy: "DM",
  reportingFiName: "",
  reportingFiAddress: "",
  reportingFiCity: "",
  reportingFiCountry: "DM",
  transmittingCountry: "DM",
  receivingCountry: "DM",
  reportingPeriod: "2025-12-31",
  currency: "USD",
  messageTypeIndic: "CRS701",
  mode: "production",
  contact: "",
  warning: "",
  defaultPaymentType: "CRS502",
  includeZeroPayments: false,
  interpretTrueAsClosed: true,
};

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "An unexpected local processing error occurred.";
}

export default function App() {
  const [step, setStep] = useState<Step>("upload");
  const [sessionId, setSessionId] = useState("");
  const [fileName, setFileName] = useState("");
  const [records, setRecords] = useState<AccountRecord[]>([]);
  const [summary, setSummary] = useState(emptySummary);
  const [schemaStatus, setSchemaStatus] = useState(initialSchema);
  const [settings, setSettings] = useState(initialSettings);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [allowDraft, setAllowDraft] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleUpload(file: File) {
    setBusy(true);
    setError("");
    try {
      const response = await uploadExcel(file);
      setSessionId(response.sessionId);
      setFileName(response.fileName);
      setRecords(response.records);
      setSummary(response.summary);
      setSchemaStatus(response.schemaStatus);
      setStep("settings");
    } catch (uploadError) {
      setError(errorMessage(uploadError));
    } finally {
      setBusy(false);
    }
  }

  async function handleValidate() {
    setBusy(true);
    setError("");
    try {
      const response = await validateRecords(sessionId, records, settings);
      setRecords(response.records);
      setSummary(response.summary);
      setStep("validation");
    } catch (validationError) {
      setError(errorMessage(validationError));
    } finally {
      setBusy(false);
    }
  }

  async function handleGenerate() {
    setBusy(true);
    setError("");
    try {
      const response = await generateXml(
        sessionId,
        records,
        settings,
        allowDraft,
      );
      setResult(response);
      setStep("preview");
    } catch (generationError) {
      setError(errorMessage(generationError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">FC</span>
          <div>
            <strong>XML Studio</strong>
            <small>FATCA / CRS v2.2</small>
          </div>
        </div>
        <div className="local-pill">
          <span />
          Local processing only
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          <div>
            <span className="sidebar-label">Workflow</span>
            {(["upload", "settings", "validation", "preview"] as Step[]).map(
              (item, index) => {
                const labels = ["Upload", "Settings", "Validation", "Download"];
                const activeIndex = ["upload", "settings", "validation", "preview"].indexOf(
                  step,
                );
                return (
                  <div
                    className={`${item === step ? "step active" : "step"} ${
                      index < activeIndex ? "complete" : ""
                    }`}
                    key={item}
                  >
                    <span>{index + 1}</span>
                    <strong>{labels[index]}</strong>
                  </div>
                );
              },
            )}
          </div>
          <div className="sidebar-file">
            <span>Current workbook</span>
            <strong>{fileName || "None selected"}</strong>
            {!!records.length && <small>{records.length} account records</small>}
          </div>
        </aside>

        <main>
          {step === "upload" && (
            <UploadPage busy={busy} error={error} onUpload={handleUpload} />
          )}
          {step === "settings" && (
            <SettingsPage
              onBack={() => setStep("upload")}
              onChange={setSettings}
              onContinue={handleValidate}
              settings={settings}
            />
          )}
          {step === "validation" && (
            <ValidationPage
              allowDraft={allowDraft}
              busy={busy}
              error={error}
              onAllowDraft={setAllowDraft}
              onBack={() => setStep("settings")}
              onGenerate={handleGenerate}
              onRecordsChange={setRecords}
              onRevalidate={handleValidate}
              records={records}
              schemaStatus={schemaStatus}
              summary={summary}
            />
          )}
          {step === "preview" && result && (
            <XmlPreviewPage
              onBack={() => setStep("validation")}
              result={result}
            />
          )}
        </main>
      </div>
    </div>
  );
}
