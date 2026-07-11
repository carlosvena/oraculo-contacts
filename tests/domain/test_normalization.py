from oraculo_contacts.domain.normalization import (
    PhoneKind,
    classify_phone,
    normalize_email,
    normalize_name,
    normalize_phone,
)


def test_normalizes_only_returned_comparison_value() -> None:
    name = "  José  Pérez "
    email = " Ada@Example.TEST "
    phone = "+54 (11) 5555-0101"
    assert normalize_name(name) == "jose perez"
    assert normalize_email(email) == "ada@example.test"
    assert normalize_phone(phone) == "1155550101"
    assert name == "  José  Pérez "
    assert email == " Ada@Example.TEST "
    assert phone == "+54 (11) 5555-0101"


def test_never_classifies_service_or_landline_as_mobile() -> None:
    assert classify_phone("0800-555-0101") is PhoneKind.TOLL_FREE
    assert classify_phone("0810-555-0101") is PhoneKind.TOLL_FREE
    assert classify_phone("011 5555-0101") is PhoneKind.LANDLINE
    assert classify_phone("+54 9 11 5555-0101") is PhoneKind.MOBILE
