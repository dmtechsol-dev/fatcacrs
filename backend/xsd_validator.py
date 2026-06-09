from __future__ import annotations

from pathlib import Path

from lxml import etree

from backend.models import SchemaValidationResult

XSD_NS = {"xsd": "http://www.w3.org/2001/XMLSchema"}


def find_missing_imports(root_schema: Path) -> list[str]:
    missing: set[str] = set()
    visited: set[Path] = set()

    def inspect(schema_path: Path) -> None:
        resolved = schema_path.resolve()
        if resolved in visited or not resolved.exists():
            return
        visited.add(resolved)
        try:
            tree = etree.parse(str(resolved))
        except (OSError, etree.XMLSyntaxError):
            return
        locations = tree.xpath(
            "//xsd:import/@schemaLocation | //xsd:include/@schemaLocation",
            namespaces=XSD_NS,
        )
        for location in locations:
            dependency = resolved.parent / str(location)
            if not dependency.exists():
                missing.add(str(location))
            else:
                inspect(dependency)

    inspect(root_schema)
    return sorted(missing)


def schema_readiness(root_schema: Path) -> SchemaValidationResult:
    missing = find_missing_imports(root_schema)
    if missing:
        return SchemaValidationResult(
            status="incomplete",
            valid=False,
            full_validation=False,
            message=(
                "Full XSD validation cannot complete until the missing "
                "schema import(s) are provided."
            ),
            missing_imports=missing,
        )
    try:
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        schema_document = etree.parse(str(root_schema), parser)
        etree.XMLSchema(schema_document)
    except (OSError, etree.XMLSchemaParseError, etree.XMLSyntaxError) as exc:
        return SchemaValidationResult(
            status="error",
            valid=False,
            full_validation=False,
            message="The XSD schema set could not be compiled.",
            errors=[str(exc)],
        )
    return SchemaValidationResult(
        status="valid",
        valid=True,
        full_validation=True,
        message="The complete XSD schema set is available and compiles.",
    )


def validate_xml(xml_content: bytes, root_schema: Path) -> SchemaValidationResult:
    try:
        xml_document = etree.fromstring(
            xml_content,
            parser=etree.XMLParser(no_network=True, resolve_entities=False),
        )
    except etree.XMLSyntaxError as exc:
        return SchemaValidationResult(
            status="invalid",
            valid=False,
            full_validation=False,
            message="Generated XML is not well-formed.",
            errors=[str(exc)],
        )

    readiness = schema_readiness(root_schema)
    if readiness.status != "valid":
        return readiness

    try:
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        schema = etree.XMLSchema(etree.parse(str(root_schema), parser))
        schema.assertValid(xml_document)
    except etree.DocumentInvalid as exc:
        errors = [
            f"Line {item.line}: {item.message}"
            for item in exc.error_log
        ]
        return SchemaValidationResult(
            status="invalid",
            valid=False,
            full_validation=True,
            message="Generated XML failed XSD validation.",
            errors=errors,
        )
    except (OSError, etree.XMLSchemaParseError, etree.XMLSyntaxError) as exc:
        return SchemaValidationResult(
            status="error",
            valid=False,
            full_validation=False,
            message="XSD validation could not be completed.",
            errors=[str(exc)],
        )

    return SchemaValidationResult(
        status="valid",
        valid=True,
        full_validation=True,
        message="Generated XML is well-formed and valid against the XSD set.",
    )
