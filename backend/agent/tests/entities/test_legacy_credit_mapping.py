from app.entities import CreditType, SubjectCredit


def test_legacy_subject_credit_mapping_preserves_credit_type_contract():
    row = SubjectCredit(
        id=1,
        subject_id=2,
        bangumi_person_id=None,
        name="制作委员会",
        role="制作",
        credit_type=CreditType.ORGANIZATION,
    )

    assert row.credit_type is CreditType.ORGANIZATION
    assert row.source_active is True
