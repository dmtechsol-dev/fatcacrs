# Local FATCA/CRS FC XML v2.2 Generator

A local-only FastAPI and React application for converting the
`Accounts to report - IRD` Excel worksheet into the customized MDES
FATCA/CRS FC XML v2.2 format.

The app parses and validates account data, supports inline corrections, builds
CRS-only individual account reports, validates generated XML against the local
XSD set, previews the XML, and downloads XML plus JSON/text validation reports.
No account data is sent to an external service.

## Current Scope

- CRS-only individual account holders
- New production data (`OECD1`) and new test data (`OECD11`)
- `CRS701`, `CRS702`, and `CRS703` message indicators
- One configurable payment type per account
- Optional zero-payment output
- Deterministic `DocRefId` values in
  `country + tax year + financial institution IN + six-digit sequence` format
- Explicit dormant, closed, and undocumented account indicators
- Optional operator-supplied `MessageRefId`
- Local `.xlsx` parsing with `openpyxl`
- XML generation and validation with `lxml`
- Explicit draft export when full XSD validation cannot complete

Organisation holders, controlling persons, nil reports, corrections, and FATCA
records are intentionally left as later extensions. `ControllingPerson` is
therefore omitted for the currently supported individual account holder flow,
as permitted by the XSD.

## Important Schema Status

The complete MDES FC XML v2.2 schema bundle is stored in `backend/schemas`,
including `isofatcatypes_v1.1.xsd`. `GET /api/health` reports schema readiness,
and every generated XML document is validated against `FatcaCrs_v2.2.xsd`
before a submission-ready download is created.

## Prerequisites

- Python 3.10+
- Node.js 20+
- npm

## Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

Set-Location frontend
npm install
Set-Location ..
```

Copy `.env.example` to `.env` only if a non-default frontend API URL is needed.
The Vite development server proxies `/api` to `http://127.0.0.1:8000`.

## Run

Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2:

```powershell
Set-Location frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Production / Coolify

The production deployment is a single Docker service. The Dockerfile builds
the React frontend and copies it into the FastAPI image, where it is served at
`/`.

Use these Coolify values:

- Build pack: `Dockerfile`
- Dockerfile: `/Dockerfile`
- Start command: leave empty
- Container port: `8000`
- Health check: `/health`
- Publish directory: leave empty
- Base directory: `/`

If a start-command override is required, use exactly:

```text
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

The ASGI path is `backend.main:app`, not `main:app`. See
[`COOLIFY.md`](COOLIFY.md) for the full deployment and domain-routing setup.
Redeploy without cache after switching the Coolify build pack.

## API

- `POST /api/upload-excel`
- `POST /api/validate`
- `POST /api/generate-xml`
- `GET /api/download/{fileId}`
- `GET /api/health`
- `GET /health`
- `GET /` (frontend in production, service JSON when no frontend build exists)

Generated files are written under `backend/data/generated/` and ignored by Git.
Uploaded workbook bytes are parsed in memory and are not persisted.

## Validation Behavior

Generation is blocked for missing required identity fields, invalid country
codes, missing or non-numeric balances, invalid dates, and duplicate generated
`DocRefId` values.

Warnings include missing TIN, missing DOB, zero balance, missing/zero payment,
and short addresses.

Data errors cannot be bypassed. Only an XSD failure or incomplete schema set can
be exported through the explicit developer/debug draft option. Draft XML
filenames are prefixed with `DRAFT_`.

`Account Status` is the workbook's dormant indicator: true means dormant and
false means active. It accepts `Yes/No`, `Y/N`, `TRUE/FALSE`, and `1/0`.
Blank or invalid values are blocking validation errors. `Dormant` and
`IsDormant` are also recognized as dedicated dormant-column aliases.

Closed and undocumented states are never inferred from `Account Status`. They
are populated only from dedicated `Closed`, `IsClosed`, `Account Closed`,
`Undocumented`, `IsUndocumented`, or `Undocumented Account` columns. When
those columns are absent, their values default to `false`. All three XSD
attributes are written on every `AccountNumber`.

Account report document references use this format:

```text
DM2025<FINANCIAL_INSTITUTION_IN><SEQUENCE>
```

The Reporting FI document uses sequence `000000`; reportable accounts start at
`000001`. The financial institution IN is resolved from an uploaded workbook
column, the app settings field, or `FINANCIAL_INSTITUTION_IN`, in that order.
It must contain only letters and digits; invalid characters are rejected
rather than silently removed.

## Tests

```powershell
python -m pytest
Set-Location frontend
npm run lint
npm run build
```

The backend tests cover workbook parsing, status aliases/defaults, missing
columns, country/balance validation, date conversion, exact and unique
`DocRefId` values, required XML sections, full XSD validation, missing import
detection, and API upload/health behavior.

## Rebuild Sample Artifacts

The sample XML is generated from the first three valid workbook rows using
`samples/sample-settings.json`. The validation report covers the complete
workbook.

```powershell
python -m backend.scripts.generate_samples `
  "C:\path\to\Copy of CRS Reportable Accounts - Year 2025 - IT Officer.xlsx"
```

The sample settings are visibly demonstrative and are not embedded in
application code. Enter the real Reporting FI values in the Settings screen
before producing an operational file.
