from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from lxml import etree

from backend.config import NS_OECD_FTC, NS_SFA, NS_SFA_FTC, NS_XSI
from backend.identifiers import (
    make_account_doc_ref_id,
    make_message_ref_id,
    make_reporting_fi_doc_ref_id,
)
from backend.models import AccountRecord, ReportingSettings
from backend.validators import parse_decimal


def q(namespace: str, local_name: str) -> etree.QName:
    return etree.QName(namespace, local_name)


def add(parent, namespace: str, name: str, text: str | None = None, **attrs):
    element = etree.SubElement(parent, q(namespace, name), **attrs)
    if text is not None:
        element.text = text
    return element


def money(value: str) -> str:
    amount = parse_decimal(value) or Decimal("0")
    return f"{amount.quantize(Decimal('0.01')):.2f}"


def build_xml(
    records: list[AccountRecord], settings: ReportingSettings
) -> tuple[bytes, str]:
    nsmap = {
        "sfa_ftc": NS_SFA_FTC,
        "oecd_ftc": NS_OECD_FTC,
        "sfa": NS_SFA,
        "xsi": NS_XSI,
    }
    root = etree.Element(
        q(NS_OECD_FTC, "FATCA_CRS"),
        nsmap=nsmap,
        version="2.2",
    )
    message_ref_id = make_message_ref_id(settings)
    header = add(root, NS_OECD_FTC, "MessageHeader")
    add(header, NS_SFA_FTC, "SendingCompanyIN", settings.sending_company_in)
    add(header, NS_SFA_FTC, "TransmittingCountry", settings.transmitting_country)
    add(header, NS_SFA_FTC, "ReceivingCountry", settings.receiving_country)
    add(header, NS_SFA_FTC, "MessageType", "FATCA-CRS")
    if settings.warning:
        add(header, NS_SFA_FTC, "Warning", settings.warning)
    if settings.contact:
        add(header, NS_SFA_FTC, "Contact", settings.contact)
    add(header, NS_SFA_FTC, "MessageRefId", message_ref_id)
    add(header, NS_SFA_FTC, "MessageTypeIndic", settings.message_type_indic)
    add(header, NS_SFA_FTC, "ReportingPeriod", settings.reporting_period)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    add(header, NS_SFA_FTC, "Timestamp", timestamp.replace("+00:00", "Z"))

    body = add(root, NS_OECD_FTC, "MessageBody")
    reporting_fi = add(body, NS_SFA_FTC, "ReportingFI")
    add(
        reporting_fi,
        NS_SFA_FTC,
        "ResCountryCode",
        settings.reporting_fi_country,
    )
    add(
        reporting_fi,
        NS_SFA_FTC,
        "TIN",
        settings.reporting_fi_tin,
        issuedBy=settings.reporting_fi_tin_issued_by,
    )
    add(reporting_fi, NS_SFA_FTC, "Name", settings.reporting_fi_name)
    fi_address = add(reporting_fi, NS_SFA_FTC, "Address")
    add(fi_address, NS_SFA, "CountryCode", settings.reporting_fi_country)
    fi_address_fix = add(fi_address, NS_SFA, "AddressFix")
    add(fi_address_fix, NS_SFA, "Street", settings.reporting_fi_address)
    add(fi_address_fix, NS_SFA, "City", settings.reporting_fi_city)
    fi_doc = add(reporting_fi, NS_SFA_FTC, "DocSpec")
    doc_type = "OECD1" if settings.mode == "production" else "OECD11"
    add(fi_doc, NS_SFA_FTC, "DocTypeIndic", doc_type)
    add(
        fi_doc,
        NS_SFA_FTC,
        "DocRefId",
        make_reporting_fi_doc_ref_id(settings),
    )

    reporting_group = add(body, NS_SFA_FTC, "ReportingGroup")
    account_doc_ref_ids = [
        make_account_doc_ref_id(settings, sequence)
        for sequence in range(1, len(records) + 1)
    ]
    if len(account_doc_ref_ids) != len(set(account_doc_ref_ids)):
        raise ValueError("Generated account DocRefId values are duplicated.")

    for record, doc_ref_id in zip(records, account_doc_ref_ids):
        account_report = add(reporting_group, NS_SFA_FTC, "AccountReport")
        doc_spec = add(account_report, NS_SFA_FTC, "DocSpec")
        add(doc_spec, NS_SFA_FTC, "DocTypeIndic", doc_type)
        add(
            doc_spec,
            NS_SFA_FTC,
            "DocRefId",
            doc_ref_id,
        )

        dormant_account = record.dormant_account or record.account_status
        account_attrs = {
            "AccNumberType": "OECD605",
            "UndocumentedAccount": str(record.undocumented_account).lower(),
            "ClosedAccount": str(record.closed_account).lower(),
            "DormantAccount": str(dormant_account).lower(),
        }
        add(
            account_report,
            NS_SFA_FTC,
            "AccountNumber",
            record.account_number,
            **account_attrs,
        )
        holder = add(account_report, NS_SFA_FTC, "AccountHolder")
        individual = add(holder, NS_SFA_FTC, "Individual")
        add(individual, NS_SFA_FTC, "ResCountryCode", record.country)
        if record.tin.strip() not in {"", "-"}:
            add(
                individual,
                NS_SFA_FTC,
                "TIN",
                record.tin,
                issuedBy=record.country,
            )
        name = add(individual, NS_SFA_FTC, "Name")
        add(name, NS_SFA, "FirstName", record.first_name)
        add(name, NS_SFA, "LastName", record.surname)
        address = add(individual, NS_SFA_FTC, "Address")
        add(address, NS_SFA, "CountryCode", record.country)
        add(address, NS_SFA, "AddressFree", record.address)
        if record.date_of_birth:
            birth_info = add(individual, NS_SFA_FTC, "BirthInfo")
            add(birth_info, NS_SFA_FTC, "BirthDate", record.date_of_birth)
        add(
            account_report,
            NS_SFA_FTC,
            "AccountBalance",
            money(record.account_balance),
            currCode=settings.currency,
        )
        payment = parse_decimal(record.payment)
        if payment is not None and (
            payment > 0 or settings.include_zero_payments
        ):
            payment_element = add(account_report, NS_SFA_FTC, "Payment")
            add(
                payment_element,
                NS_SFA_FTC,
                "Type",
                settings.default_payment_type,
            )
            add(
                payment_element,
                NS_SFA_FTC,
                "PaymentAmnt",
                money(record.payment),
                currCode=settings.currency,
            )

    content = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )
    return content, message_ref_id
