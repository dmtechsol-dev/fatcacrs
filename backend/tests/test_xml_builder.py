from lxml import etree

from backend.config import NS_SFA_FTC, ROOT_SCHEMA
from backend.models import AccountRecord
from backend.xml_builder import build_xml
from backend.xsd_validator import validate_xml


def sample_record(row_number: int, account: str):
    return AccountRecord(
        row_number=row_number,
        account_number=account,
        first_name="Ada",
        surname="Lovelace",
        date_of_birth="1815-12-10",
        address="1 Analytical Engine Way",
        country="GB",
        tin="GB-TIN-1",
        account_status=False,
        payment="15.25",
        account_balance="1000",
    )


def test_xml_is_well_formed_and_uses_expected_elements(settings):
    content, message_ref = build_xml([sample_record(2, "A-1")], settings)
    root = etree.fromstring(content)
    assert root.tag == "{urn:fatcacrs:ties:v2}FATCA_CRS"
    assert root.get("version") == "2.2"
    assert message_ref.startswith("DM2025DEMO123")
    assert not root.xpath("//*[local-name()='Payment2']")
    assert root.xpath("count(//*[local-name()='Payment'])") == 1.0
    account_number = root.find(f".//{{{NS_SFA_FTC}}}AccountNumber")
    assert account_number is not None
    assert account_number.get("ClosedAccount") == "false"
    assert account_number.get("DormantAccount") == "false"
    assert account_number.get("UndocumentedAccount") == "false"


def test_doc_ref_ids_are_unique(settings):
    content, _ = build_xml(
        [sample_record(2, "A-1"), sample_record(3, "A-1")],
        settings,
    )
    root = etree.fromstring(content)
    refs = [
        element.text
        for element in root.xpath("//*[local-name()='DocRefId']")
    ]
    assert len(refs) == len(set(refs))
    assert refs == [
        "DM2025FIIN000000",
        "DM2025FIIN000001",
        "DM2025FIIN000002",
    ]


def test_required_template_elements_and_statuses_validate(settings):
    record = sample_record(2, "A-1").model_copy(
        update={
            "account_status": False,
            "closed_account": True,
            "dormant_account": True,
            "undocumented_account": True,
        }
    )
    content, _ = build_xml([record], settings)
    root = etree.fromstring(content)

    required_paths = [
        "MessageHeader/SendingCompanyIN",
        "MessageHeader/MessageRefId",
        "MessageHeader/ReportingPeriod",
        "MessageBody/ReportingFI/TIN",
        "MessageBody/ReportingFI/DocSpec/DocTypeIndic",
        "MessageBody/ReportingFI/DocSpec/DocRefId",
        "MessageBody/ReportingGroup/AccountReport/DocSpec/DocTypeIndic",
        "MessageBody/ReportingGroup/AccountReport/DocSpec/DocRefId",
        "MessageBody/ReportingGroup/AccountReport/AccountNumber",
        "MessageBody/ReportingGroup/AccountReport/AccountHolder/Individual/Name",
        "MessageBody/ReportingGroup/AccountReport/AccountHolder/Individual/Address",
        "MessageBody/ReportingGroup/AccountReport/AccountBalance",
        "MessageBody/ReportingGroup/AccountReport/Payment",
    ]
    for path in required_paths:
        local_path = ".//" + "/".join(
            f"*[local-name()='{part}']" for part in path.split("/")
        )
        assert root.xpath(local_path), path

    account_number = root.xpath(
        "//*[local-name()='AccountNumber']"
    )[0]
    assert account_number.attrib == {
        "AccNumberType": "OECD605",
        "UndocumentedAccount": "true",
        "ClosedAccount": "true",
        "DormantAccount": "true",
    }
    schema_result = validate_xml(content, ROOT_SCHEMA)
    assert schema_result.valid, schema_result.errors


def test_legacy_account_status_sets_only_dormant_attribute(settings):
    record = sample_record(2, "A-1").model_copy(
        update={
            "account_status": True,
            "dormant_account": True,
            "closed_account": False,
            "undocumented_account": False,
        }
    )
    content, _ = build_xml([record], settings)
    account_number = etree.fromstring(content).xpath(
        "//*[local-name()='AccountNumber']"
    )[0]
    assert account_number.get("DormantAccount") == "true"
    assert account_number.get("ClosedAccount") == "false"
    assert account_number.get("UndocumentedAccount") == "false"
