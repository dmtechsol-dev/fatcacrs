from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.financial_institution import normalize_financial_institution_in


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class AccountRecord(ApiModel):
    row_number: int
    account_number: str = ""
    first_name: str = ""
    surname: str = ""
    date_of_birth: str = ""
    address: str = ""
    country: str = ""
    tin: str = ""
    account_status: bool = False
    dormant_account: bool = False
    closed_account: bool = False
    undocumented_account: bool = False
    status_error: str = ""
    payment: str = ""
    account_balance: str = ""
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReportingSettings(ApiModel):
    sending_company_in: str = Field(min_length=1, max_length=200)
    financial_institution_in: str = Field(default="", max_length=188)
    reporting_fi_tin: str = Field(min_length=1, max_length=200)
    reporting_fi_tin_issued_by: str = "DM"
    reporting_fi_name: str = Field(min_length=1, max_length=200)
    reporting_fi_address: str = Field(min_length=1, max_length=200)
    reporting_fi_city: str = Field(min_length=1, max_length=200)
    reporting_fi_country: str = "DM"
    transmitting_country: str = "DM"
    receiving_country: str = "DM"
    tax_year: str = "2025"
    reporting_period: str = "2025-12-31"
    message_ref_id: str = Field(default="", max_length=200)
    currency: str = Field(min_length=3, max_length=3)
    message_type_indic: Literal["CRS701", "CRS702", "CRS703"] = "CRS701"
    mode: Literal["production", "test"] = "production"
    contact: str = Field(default="", max_length=200)
    warning: str = Field(default="", max_length=4000)
    default_payment_type: Literal["CRS501", "CRS502", "CRS503", "CRS504"] = "CRS502"
    include_zero_payments: bool = False

    @field_validator(
        "reporting_fi_tin_issued_by",
        "reporting_fi_country",
        "transmitting_country",
        "receiving_country",
    )
    @classmethod
    def validate_country(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 2 or not value.isalpha():
            raise ValueError("must be exactly two uppercase letters")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("must be a three-letter currency code")
        return value

    @field_validator("tax_year")
    @classmethod
    def validate_tax_year(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"\d{4}", value):
            raise ValueError("must be exactly four digits")
        return value

    @field_validator("reporting_fi_tin")
    @classmethod
    def validate_reporting_fi_tin(cls, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]", "", value)
        if not normalized:
            raise ValueError("must contain at least one letter or digit")
        if len(normalized) > 189:
            raise ValueError(
                "is too long for the required 200-character DocRefId"
            )
        return value

    @field_validator("financial_institution_in")
    @classmethod
    def validate_financial_institution_in(cls, value: str) -> str:
        if not value:
            return ""
        return normalize_financial_institution_in(
            value,
            source="Configured financial institution IN",
        )

    @model_validator(mode="after")
    def validate_reporting_period_year(self):
        try:
            reporting_date = date.fromisoformat(self.reporting_period)
        except ValueError as exc:
            raise ValueError(
                "reportingPeriod must be a date in YYYY-MM-DD format"
            ) from exc
        if str(reporting_date.year) != self.tax_year:
            raise ValueError(
                "taxYear must match the year in reportingPeriod"
            )
        return self


class ValidationSummary(ApiModel):
    total_records: int = 0
    valid_records: int = 0
    error_records: int = 0
    warning_records: int = 0
    country_breakdown: dict[str, int] = Field(default_factory=dict)
    closed_accounts: int = 0
    open_accounts: int = 0
    dormant_accounts: int = 0
    undocumented_accounts: int = 0
    missing_tin: int = 0
    missing_dob: int = 0
    missing_balance: int = 0


class SchemaValidationResult(ApiModel):
    status: Literal["valid", "invalid", "incomplete", "error"]
    valid: bool
    full_validation: bool
    message: str
    errors: list[str] = Field(default_factory=list)
    missing_imports: list[str] = Field(default_factory=list)


class StatusMappingInfo(ApiModel):
    account_status: str | None = None
    dormant_account: str | None = None
    closed_account: str | None = None
    undocumented_account: str | None = None
    warnings: list[str] = Field(default_factory=list)


class UploadResponse(ApiModel):
    session_id: str
    file_name: str
    financial_institution_in: str | None = None
    records: list[AccountRecord]
    summary: ValidationSummary
    schema_status: SchemaValidationResult
    status_mapping: StatusMappingInfo


class ValidateRequest(ApiModel):
    session_id: str | None = None
    records: list[AccountRecord]
    settings: ReportingSettings | None = None


class ValidationResponse(ApiModel):
    records: list[AccountRecord]
    summary: ValidationSummary
    can_generate: bool


class GenerateRequest(ApiModel):
    session_id: str | None = None
    records: list[AccountRecord]
    settings: ReportingSettings
    allow_draft: bool = False


class DownloadArtifact(ApiModel):
    file_id: str
    file_name: str


class GenerationResponse(ApiModel):
    message_ref_id: str
    xml_preview: str
    xml: DownloadArtifact
    validation_json: DownloadArtifact
    validation_text: DownloadArtifact
    schema_validation: SchemaValidationResult
    draft: bool
