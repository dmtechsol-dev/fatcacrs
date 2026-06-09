from pathlib import Path

from backend.xsd_validator import find_missing_imports, validate_xml


def test_missing_import_is_detected(tmp_path: Path):
    schema = tmp_path / "root.xsd"
    schema.write_text(
        """<?xml version="1.0"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:include schemaLocation="missing.xsd"/>
</xsd:schema>
""",
        encoding="utf-8",
    )
    assert find_missing_imports(schema) == ["missing.xsd"]
    result = validate_xml(b"<root/>", schema)
    assert result.status == "incomplete"
    assert not result.valid


def test_xsd_validation_success_and_failure(tmp_path: Path):
    schema = tmp_path / "root.xsd"
    schema.write_text(
        """<?xml version="1.0"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:element name="root">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="value" type="xsd:string"/>
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>
""",
        encoding="utf-8",
    )
    success = validate_xml(b"<root><value>ok</value></root>", schema)
    failure = validate_xml(b"<root><wrong/></root>", schema)
    assert success.status == "valid"
    assert success.valid
    assert failure.status == "invalid"
    assert not failure.valid
