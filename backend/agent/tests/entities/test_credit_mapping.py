from app.entities import CreditType, SubjectPersonCredit


def test_unresolved_credit_maps_to_placeholder_row():
    row = SubjectPersonCredit(
        id=1,
        subject_id=2,
        person_id=None,
        name="制作委员会",
        credit_type=CreditType.ORGANIZATION,
        role="制作",
    )

    assert row.person_id is None
    assert row.name == "制作委员会"
    assert row.credit_type is CreditType.ORGANIZATION


def test_resolved_credit_has_fk_and_no_placeholder_name():
    row = SubjectPersonCredit(
        id=3,
        subject_id=2,
        person_id=42,
        name=None,
        credit_type=CreditType.PERSON,
        role="导演",
    )

    assert row.person_id == 42
    assert row.name is None
    assert row.credit_type is CreditType.PERSON
