import type {
  AccountRecord,
  GenerationResult,
  SchemaValidation,
  Settings,
  StatusMapping,
  Summary,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

type ApiErrorPayload = {
  detail?:
    | string
    | Array<{ loc?: Array<string | number>; msg?: string }>
    | { message?: string; schemaValidation?: SchemaValidation };
};

export class ApiError extends Error {
  payload: ApiErrorPayload;

  constructor(message: string, payload: ApiErrorPayload) {
    super(message);
    this.payload = payload;
  }
}

async function readResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }
  const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
  const detail = payload.detail;
  let message =
    typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail
            .map((item) => {
              const field = item.loc?.slice(1).join(".");
              return `${field ? `${field}: ` : ""}${item.msg ?? "Invalid value."}`;
            })
            .join(" ")
        : detail?.message ?? `Request failed with status ${response.status}.`;
  if (
    detail &&
    typeof detail !== "string" &&
    !Array.isArray(detail) &&
    detail.schemaValidation?.errors.length
  ) {
    message = `${message} ${detail.schemaValidation.errors.slice(0, 3).join(" ")}`;
  }
  throw new ApiError(message, payload);
}

export async function uploadExcel(file: File) {
  const form = new FormData();
  form.append("file", file);
  return readResponse<{
    sessionId: string;
    fileName: string;
    financialInstitutionIn: string | null;
    records: AccountRecord[];
    summary: Summary;
    schemaStatus: SchemaValidation;
    statusMapping: StatusMapping;
  }>(
    await fetch(`${API_BASE}/api/upload-excel`, {
      method: "POST",
      body: form,
    }),
  );
}

export async function validateRecords(
  sessionId: string,
  records: AccountRecord[],
  settings: Settings,
) {
  return readResponse<{
    records: AccountRecord[];
    summary: Summary;
    canGenerate: boolean;
  }>(
    await fetch(`${API_BASE}/api/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, records, settings }),
    }),
  );
}

export async function generateXml(
  sessionId: string,
  records: AccountRecord[],
  settings: Settings,
  allowDraft: boolean,
) {
  return readResponse<GenerationResult>(
    await fetch(`${API_BASE}/api/generate-xml`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, records, settings, allowDraft }),
    }),
  );
}

export function downloadUrl(fileId: string) {
  return `${API_BASE}/api/download/${encodeURIComponent(fileId)}`;
}
