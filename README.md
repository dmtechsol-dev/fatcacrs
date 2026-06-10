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
- Local `.xlsx` parsing with `openpyxl`
- XML generation and validation with `lxml`
- Explicit draft export when full XSD validation cannot complete

Organisation holders, controlling persons, nil reports, corrections, and FATCA
records are intentionally left as later extensions.

## Important Schema Status

The supplied main schema directory does not contain
`isofatcatypes_v1.1.xsd`, although both `FatcaCrsTypes_v2.2.xsd` and
`stffatcatypes_v2.0.xsd` import it.

The application therefore reports schema validation as **incomplete**. It does
not claim that XML passed full XSD validation. To enable full validation, place
the official file here:

```text
backend/schemas/isofatcatypes_v1.1.xsd
```

Then restart the backend. `GET /api/health` will report whether the complete
schema set compiles.

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

If a start-command override is required, use exactly:

```text
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

The ASGI path is `backend.main:app`, not `main:app`. See
[`COOLIFY.md`](COOLIFY.md) for the full deployment and domain-routing setup.

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
be exported through the explicit draft option. Draft XML filenames are prefixed
with `DRAFT_`.

## Tests

```powershell
python -m pytest
Set-Location frontend
npm run lint
npm run build
```

The backend tests cover workbook parsing, summary-row removal, country/balance
validation, date conversion, well-formed XML, unique `DocRefId` values, XSD
success/failure, missing import detection, and API upload/health behavior.

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
