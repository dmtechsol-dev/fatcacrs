export type AccountRecord = {
  rowNumber: number;
  accountNumber: string;
  firstName: string;
  surname: string;
  dateOfBirth: string;
  address: string;
  country: string;
  tin: string;
  accountStatus: boolean;
  dormantAccount: boolean;
  closedAccount: boolean;
  undocumentedAccount: boolean;
  statusError: string;
  payment: string;
  accountBalance: string;
  errors: string[];
  warnings: string[];
};

export type Summary = {
  totalRecords: number;
  validRecords: number;
  errorRecords: number;
  warningRecords: number;
  countryBreakdown: Record<string, number>;
  closedAccounts: number;
  openAccounts: number;
  dormantAccounts: number;
  undocumentedAccounts: number;
  missingTin: number;
  missingDob: number;
  missingBalance: number;
};

export type SchemaValidation = {
  status: "valid" | "invalid" | "incomplete" | "error";
  valid: boolean;
  fullValidation: boolean;
  message: string;
  errors: string[];
  missingImports: string[];
};

export type Settings = {
  sendingCompanyIn: string;
  reportingFiTin: string;
  reportingFiTinIssuedBy: string;
  reportingFiName: string;
  reportingFiAddress: string;
  reportingFiCity: string;
  reportingFiCountry: string;
  transmittingCountry: string;
  receivingCountry: string;
  taxYear: string;
  reportingPeriod: string;
  messageRefId: string;
  currency: string;
  messageTypeIndic: "CRS701" | "CRS702" | "CRS703";
  mode: "production" | "test";
  contact: string;
  warning: string;
  defaultPaymentType: "CRS501" | "CRS502" | "CRS503" | "CRS504";
  includeZeroPayments: boolean;
  interpretTrueAsClosed: boolean;
};

export type StatusMapping = {
  accountStatus: string | null;
  dormantAccount: string | null;
  closedAccount: string | null;
  undocumentedAccount: string | null;
  warnings: string[];
};

export type Artifact = {
  fileId: string;
  fileName: string;
};

export type GenerationResult = {
  messageRefId: string;
  xmlPreview: string;
  xml: Artifact;
  validationJson: Artifact;
  validationText: Artifact;
  schemaValidation: SchemaValidation;
  draft: boolean;
};
