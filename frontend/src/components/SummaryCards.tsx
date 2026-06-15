import type { Summary } from "../types";

type Props = {
  summary: Summary;
};

const cards: Array<[keyof Summary, string, string]> = [
  ["totalRecords", "Parsed records", "neutral"],
  ["validRecords", "Valid records", "success"],
  ["errorRecords", "Error records", "danger"],
  ["warningRecords", "Warning records", "warning"],
  ["closedAccounts", "Closed accounts", "neutral"],
  ["openAccounts", "Open accounts", "neutral"],
  ["dormantAccounts", "Dormant accounts", "neutral"],
  ["undocumentedAccounts", "Undocumented", "warning"],
  ["missingTin", "Missing TIN", "warning"],
  ["missingDob", "Missing DOB", "warning"],
  ["missingBalance", "Missing balance", "danger"],
];

export function SummaryCards({ summary }: Props) {
  return (
    <div className="summary-grid">
      {cards.map(([key, label, tone]) => (
        <article className={`summary-card ${tone}`} key={key}>
          <span>{label}</span>
          <strong>{String(summary[key])}</strong>
        </article>
      ))}
    </div>
  );
}
