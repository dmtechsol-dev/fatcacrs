import type { Settings, StatusMapping } from "../types";

type Props = {
  settings: Settings;
  statusMapping: StatusMapping;
  onChange: (settings: Settings) => void;
  onBack: () => void;
  onContinue: () => void;
};

type TextField = Exclude<
  keyof Settings,
  | "includeZeroPayments"
  | "mode"
  | "messageTypeIndic"
  | "defaultPaymentType"
>;

const fields: Array<{
  key: TextField;
  label: string;
  placeholder?: string;
  type?: string;
  required?: boolean;
}> = [
  { key: "sendingCompanyIn", label: "SendingCompanyIN", required: true },
  {
    key: "financialInstitutionIn",
    label: "Financial institution IN (DocRefId)",
    placeholder: "Uses uploaded workbook or server environment when blank",
  },
  { key: "reportingFiTin", label: "Reporting FI TIN", required: true },
  {
    key: "reportingFiTinIssuedBy",
    label: "Reporting FI TIN issuedBy",
    required: true,
  },
  { key: "reportingFiName", label: "Reporting FI name", required: true },
  { key: "reportingFiAddress", label: "Reporting FI address", required: true },
  { key: "reportingFiCity", label: "Reporting FI city", required: true },
  { key: "reportingFiCountry", label: "Reporting FI country", required: true },
  { key: "transmittingCountry", label: "TransmittingCountry", required: true },
  { key: "receivingCountry", label: "ReceivingCountry", required: true },
  { key: "taxYear", label: "Tax year", required: true },
  {
    key: "reportingPeriod",
    label: "ReportingPeriod",
    type: "date",
    required: true,
  },
  {
    key: "messageRefId",
    label: "MessageRefId (optional)",
    placeholder: "Generated automatically when blank",
  },
  { key: "currency", label: "Currency", placeholder: "USD", required: true },
  { key: "contact", label: "Contact (optional)" },
  { key: "warning", label: "Warning (optional)" },
];

export function SettingsPage({
  settings,
  statusMapping,
  onChange,
  onBack,
  onContinue,
}: Props) {
  const requiredComplete = fields
    .filter((field) => field.required)
    .every((field) => settings[field.key].trim());

  function set<K extends keyof Settings>(key: K, value: Settings[K]) {
    onChange({ ...settings, [key]: value });
  }

  return (
    <section className="page-card">
      <div className="eyebrow">Step 2 of 4</div>
      <h1>Reporting institution settings</h1>
      <p className="page-intro">
        These values populate the message header and ReportingFI section. They
        are never replaced with sample institution data.
      </p>
      <div className="form-grid">
        {fields.map((field) => (
          <label
            className={field.key === "warning" ? "field span-2" : "field"}
            key={field.key}
          >
            <span>
              {field.label}
              {field.required && <b> *</b>}
            </span>
            <input
              maxLength={
                field.key === "taxYear"
                  ? 4
                  : field.key === "financialInstitutionIn"
                    ? 188
                  : field.key.toLowerCase().includes("country") ||
                field.key === "reportingFiTinIssuedBy"
                  ? 2
                  : field.key === "currency"
                    ? 3
                    : undefined
              }
              onChange={(event) =>
                set(
                  field.key,
                  (
                    field.key.toLowerCase().includes("country") ||
                    field.key === "reportingFiTinIssuedBy" ||
                    field.key === "financialInstitutionIn" ||
                    field.key === "currency"
                      ? event.target.value.toUpperCase()
                      : event.target.value
                  ) as Settings[typeof field.key],
                )
              }
              placeholder={field.placeholder}
              required={field.required}
              type={field.type ?? "text"}
              value={settings[field.key]}
            />
          </label>
        ))}
        <label className="field">
          <span>MessageTypeIndic</span>
          <select
            onChange={(event) =>
              set(
                "messageTypeIndic",
                event.target.value as Settings["messageTypeIndic"],
              )
            }
            value={settings.messageTypeIndic}
          >
            <option value="CRS701">CRS701 - New data</option>
            <option value="CRS702">CRS702 - Correction</option>
            <option value="CRS703">CRS703 - No data</option>
          </select>
        </label>
        <label className="field">
          <span>Submission mode</span>
          <select
            onChange={(event) =>
              set("mode", event.target.value as Settings["mode"])
            }
            value={settings.mode}
          >
            <option value="production">Production - OECD1</option>
            <option value="test">Test - OECD11</option>
          </select>
        </label>
        <label className="field">
          <span>Default payment type</span>
          <select
            onChange={(event) =>
              set(
                "defaultPaymentType",
                event.target.value as Settings["defaultPaymentType"],
              )
            }
            value={settings.defaultPaymentType}
          >
            <option value="CRS501">CRS501 - Dividends</option>
            <option value="CRS502">CRS502 - Interest</option>
            <option value="CRS503">CRS503 - Gross proceeds</option>
            <option value="CRS504">CRS504 - Other</option>
          </select>
        </label>
        <div className="check-stack">
          <label className="check-field">
            <input
              checked={settings.includeZeroPayments}
              onChange={(event) =>
                set("includeZeroPayments", event.target.checked)
              }
              type="checkbox"
            />
            Include zero payment entries
          </label>
        </div>
      </div>
      <div className="mapping-panel">
        <div>
          <strong>Detected account status columns</strong>
          <p>
            Account Status supplies the required dormant value. Missing
            dedicated closed or undocumented indicators default to{" "}
            <code>false</code>. The generated AccountNumber always includes
            all three XSD status attributes.
          </p>
        </div>
        <div className="mapping-list">
          {[
            ["Dormant: Account Status", statusMapping.accountStatus],
            ["Dormant: dedicated column", statusMapping.dormantAccount],
            ["ClosedAccount", statusMapping.closedAccount],
            ["UndocumentedAccount", statusMapping.undocumentedAccount],
          ].map(([label, source]) => (
            <span className={source ? "mapped" : "unmapped"} key={label}>
              <b>{label}</b>
              {source ?? "Not detected"}
            </span>
          ))}
        </div>
        {statusMapping.warnings.map((warning) => (
          <div className="mapping-warning" key={warning}>
            {warning}
          </div>
        ))}
      </div>
      <div className="action-row">
        <button className="secondary" onClick={onBack} type="button">
          Back
        </button>
        <button
          className="primary"
          disabled={!requiredComplete}
          onClick={onContinue}
          type="button"
        >
          Validate account records
        </button>
      </div>
    </section>
  );
}
