import { useMemo, useState } from "react";
import type { AccountRecord } from "../types";

type Filter = "all" | "valid" | "errors" | "warnings";
type EditableField =
  | "country"
  | "dateOfBirth"
  | "tin"
  | "accountBalance"
  | "address"
  | "payment";

type Props = {
  records: AccountRecord[];
  onChange: (records: AccountRecord[]) => void;
};

const PAGE_SIZE = 50;

export function ValidationTable({ records, onChange }: Props) {
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    if (filter === "valid") return records.filter((record) => !record.errors.length);
    if (filter === "errors") return records.filter((record) => record.errors.length);
    if (filter === "warnings")
      return records.filter((record) => record.warnings.length);
    return records;
  }, [filter, records]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const activePage = Math.min(page, pageCount);
  const visible = filtered.slice(
    (activePage - 1) * PAGE_SIZE,
    activePage * PAGE_SIZE,
  );

  function update(rowNumber: number, field: EditableField, value: string) {
    onChange(
      records.map((record) =>
        record.rowNumber === rowNumber
          ? { ...record, [field]: value }
          : record,
      ),
    );
  }

  function chooseFilter(value: Filter) {
    setFilter(value);
    setPage(1);
  }

  return (
    <div className="table-shell">
      <div className="table-toolbar">
        <div className="filter-group" aria-label="Validation filters">
          {(["all", "valid", "errors", "warnings"] as Filter[]).map((value) => (
            <button
              className={filter === value ? "filter active" : "filter"}
              key={value}
              onClick={() => chooseFilter(value)}
              type="button"
            >
              {value[0].toUpperCase() + value.slice(1)}
            </button>
          ))}
        </div>
        <span>{filtered.length} rows shown</span>
      </div>
      <div className="table-scroll">
        <table className="validation-table">
          <thead>
            <tr>
              <th>Row</th>
              <th>Account</th>
              <th>Name</th>
              <th>Country</th>
              <th>DOB</th>
              <th>TIN</th>
              <th>Balance</th>
              <th>Payment</th>
              <th>Address</th>
              <th>Status</th>
              <th>Findings</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((record) => (
              <tr
                className={record.errors.length ? "row-error" : ""}
                key={record.rowNumber}
              >
                <td>{record.rowNumber}</td>
                <td>{record.accountNumber}</td>
                <td>
                  <strong>
                    {record.firstName} {record.surname}
                  </strong>
                </td>
                <td>
                  <input
                    aria-label={`Country row ${record.rowNumber}`}
                    className="compact-input country-input"
                    maxLength={2}
                    onChange={(event) =>
                      update(
                        record.rowNumber,
                        "country",
                        event.target.value.toUpperCase(),
                      )
                    }
                    value={record.country}
                  />
                </td>
                <td>
                  <input
                    aria-label={`Date of birth row ${record.rowNumber}`}
                    className="compact-input date-input"
                    onChange={(event) =>
                      update(record.rowNumber, "dateOfBirth", event.target.value)
                    }
                    type="date"
                    value={record.dateOfBirth}
                  />
                </td>
                <td>
                  <input
                    aria-label={`TIN row ${record.rowNumber}`}
                    className="compact-input"
                    onChange={(event) =>
                      update(record.rowNumber, "tin", event.target.value)
                    }
                    value={record.tin}
                  />
                </td>
                <td>
                  <input
                    aria-label={`Balance row ${record.rowNumber}`}
                    className="compact-input amount-input"
                    inputMode="decimal"
                    onChange={(event) =>
                      update(
                        record.rowNumber,
                        "accountBalance",
                        event.target.value,
                      )
                    }
                    value={record.accountBalance}
                  />
                </td>
                <td>
                  <input
                    aria-label={`Payment row ${record.rowNumber}`}
                    className="compact-input amount-input"
                    inputMode="decimal"
                    onChange={(event) =>
                      update(record.rowNumber, "payment", event.target.value)
                    }
                    value={record.payment}
                  />
                </td>
                <td>
                  <textarea
                    aria-label={`Address row ${record.rowNumber}`}
                    className="compact-input address-input"
                    onChange={(event) =>
                      update(record.rowNumber, "address", event.target.value)
                    }
                    rows={2}
                    value={record.address}
                  />
                </td>
                <td>
                  <span
                    className={
                      record.accountStatus ? "status closed" : "status open"
                    }
                  >
                    {record.accountStatus ? "Closed" : "Open"}
                  </span>
                </td>
                <td className="findings-cell">
                  {record.errors.map((error) => (
                    <span className="finding error" key={error}>
                      {error}
                    </span>
                  ))}
                  {record.warnings.map((warning) => (
                    <span className="finding warning" key={warning}>
                      {warning}
                    </span>
                  ))}
                  {!record.errors.length && !record.warnings.length && (
                    <span className="finding good">Ready</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="pagination">
        <button
          disabled={activePage === 1}
          onClick={() => setPage((value) => Math.max(1, value - 1))}
          type="button"
        >
          Previous
        </button>
        <span>
          Page {activePage} of {pageCount}
        </span>
        <button
          disabled={activePage === pageCount}
          onClick={() => setPage((value) => Math.min(pageCount, value + 1))}
          type="button"
        >
          Next
        </button>
      </div>
    </div>
  );
}
