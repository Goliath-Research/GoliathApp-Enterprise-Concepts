"""Course lab data: the fictional acme_child company (synthetic, labelled, local lab only).

Everything is created through GoliathApp's own platform functions and session APIs, the same way an
operator or a descendant application would. Nothing here is customer or tenant data: every name says
"(course lab)" and every email uses the reserved .invalid domain.
"""

from __future__ import annotations

from dataclasses import dataclass

ORG_A = "AcmeChild Instruments (course lab)"
ORG_B = "Bench Partners (course lab)"
OPERATOR_ROLE = "acme_child_operator"
OPERATOR_PERMISSIONS = ("meta.schema.read", "meta.object.read", "meta.object.write")


@dataclass(frozen=True)
class CourseUser:
    key: str
    email: str
    full_name: str


USERS = (
    CourseUser("admin", "ada.admin@acme-child.course.invalid", "Ada Admin (course lab)"),
    CourseUser("operator", "oscar.operator@acme-child.course.invalid", "Oscar Operator (course lab)"),
    CourseUser("outsider", "olivia.outsider@bench-partners.course.invalid", "Olivia Outsider (course lab)"),
)

# acme_child Meta classes under platform parents: (class, parent, [(field, type, required)]).
CLASSES = (
    (
        "acme_child/Instrument",
        "platform/Item",
        [
            ("Label", "platform/catalog/Text", True),
            ("SerialNumber", "platform/catalog/Text", True),
            ("Model", "platform/catalog/Text", False),
            ("CalibrationIntervalDays", "platform/catalog/Integer", False),
        ],
    ),
    (
        "acme_child/CalibrationRun",
        "platform/Batch",
        [
            ("Label", "platform/catalog/Text", True),
            ("InstrumentSerial", "platform/catalog/Text", True),
            ("PerformedOn", "platform/catalog/Date", False),
            ("Result", "platform/catalog/Text", False),
            ("DeviationPercent", "platform/catalog/Decimal", False),
        ],
    ),
)

INSTRUMENTS = (
    {"Label": "Bench scale A (course lab)", "SerialNumber": "ACME-SC-0001", "Model": "Scale 200", "CalibrationIntervalDays": 90},
    {"Label": "Bench scale B (course lab)", "SerialNumber": "ACME-SC-0002", "Model": "Scale 200", "CalibrationIntervalDays": 90},
    {"Label": "Thermometer 1 (course lab)", "SerialNumber": "ACME-TH-0001", "Model": "Therm 10", "CalibrationIntervalDays": 180},
)

OUTSIDER_INSTRUMENTS = (
    {"Label": "Partner pipette (course lab)", "SerialNumber": "BENCH-PP-0001", "Model": "Pipette 5"},
)
