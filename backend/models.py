from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    payment: str = ""
    account_balance: str = ""
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReportingSettings(ApiModel):
    sending_company_in: str = Field(min_length=1, max_length=200)
    reporting_fi_tin: str = Field(min_length=1, max_length=200)
    reporting_fi_tin_issued_by: str = "DM"
    reporting_fi_name: str = Field(min_length=1, max_length=200)
    reporting_fi_address: str = Field(min_length=1, max_length=200)
    reporting_fi_city: str = Field(min_length=1, max_length=200)
    reporting_fi_country: str = "DM"
    transmitting_country: str = "DM"
    receiving_country: str = "DM"
    reporting_period: str = "2025-12-31"
    currency: str = Field(min_length=3, max_length=3)
    message_type_indic: Literal["CRS701", "CRS702", "CRS703"] = "CRS701"
    mode: Literal["production", "test"] = "production"
    contact: str = Field(default="", max_length=200)
    warning: str = Field(default="", max_length=4000)
    default_payment_type: Literal["CRS501", "CRS502", "CRS503", "CRS504"] = "CRS502"
    include_zero_payments: bool = False
    interpret_true_as_closed: bool = True

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


class ValidationSummary(ApiModel):
    total_records: int = 0
    valid_records: int = 0
    error_records: int = 0
    warning_records: int = 0
    country_breakdown: dict[str, int] = Field(default_factory=dict)
    closed_accounts: int = 0
    open_accounts: int = 0
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


class UploadResponse(ApiModel):
    session_id: str
    file_name: str
    records: list[AccountRecord]
    summary: ValidationSummary
    schema_status: SchemaValidationResult


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
