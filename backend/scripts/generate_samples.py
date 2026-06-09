from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.config import ROOT_SCHEMA
from backend.excel_parser import parse_excel_bytes
from backend.models import ReportingSettings
from backend.validators import build_summary, validate_records
from backend.xml_builder import build_xml
from backend.xsd_validator import validate_xml


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate reproducible sample artifacts from a workbook."
    )
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--settings",
        type=Path,
        default=Path("samples/sample-settings.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("samples"),
    )
    args = parser.parse_args()

    settings = ReportingSettings.model_validate_json(
        args.settings.read_text(encoding="utf-8")
    )
    records = validate_records(parse_excel_bytes(args.workbook.read_bytes()), settings)
    summary = build_summary(records)
    valid_records = [record for record in records if not record.errors]
    sample_records = valid_records[:3]
    xml_content, message_ref_id = build_xml(sample_records, settings)
    schema_result = validate_xml(xml_content, ROOT_SCHEMA)

    report = {
        "sourceWorkbook": args.workbook.name,
        "messageRefId": message_ref_id,
        "sampleXmlRecordCount": len(sample_records),
        "summary": summary.model_dump(by_alias=True),
        "schemaValidation": schema_result.model_dump(by_alias=True),
        "records": [
            {
                "rowNumber": record.row_number,
                "accountNumber": record.account_number,
                "errors": record.errors,
                "warnings": record.warnings,
            }
            for record in records
        ],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "sample-generated.xml").write_bytes(xml_content)
    (args.output / "sample-validation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    text_lines = [
        "Attached Workbook Validation Summary",
        "=" * 38,
        f"Total records: {summary.total_records}",
        f"Valid records: {summary.valid_records}",
        f"Error records: {summary.error_records}",
        f"Warning records: {summary.warning_records}",
        f"Sample XML records: {len(sample_records)}",
        f"Schema status: {schema_result.status}",
        schema_result.message,
    ]
    if schema_result.missing_imports:
        text_lines.append(
            "Missing imports: " + ", ".join(schema_result.missing_imports)
        )
    (args.output / "sample-validation-report.txt").write_text(
        "\n".join(text_lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
