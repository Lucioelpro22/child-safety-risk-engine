from risk_engine import RiskEngine, RiskLevel, analyze


def test_clean_message_has_no_signal_and_does_not_claim_safe():
    result = analyze("How was school today?")
    assert result.level is RiskLevel.LOW
    assert result.score == 0
    assert result.signals == ()
    assert "not proof of safety" in result.explanation


def test_secrecy_is_explainable_and_does_not_leak_message():
    result = analyze("Don't tell your parents, keep this secret.")
    assert result.level is RiskLevel.MEDIUM
    assert [s.signal_id for s in result.signals] == ["secrecy_request"]
    assert result.signals[0].evidence_count == 2
    assert "Don't tell" not in result.as_dict()["explanation"]


def test_multiple_categories_escalate_to_critical():
    result = analyze("Don't tell your mom. Send the nude or I'll send it to everyone.")
    assert result.level is RiskLevel.CRITICAL
    assert {s.signal_id for s in result.signals} == {"secrecy_request", "sexual_escalation", "sextortion"}
    assert result.score >= 0.75


def test_spanish_accents_are_normalized():
    result = analyze("No le cuentes a tus padres, mantenelo en secreto.")
    assert "secrecy_request" in {s.signal_id for s in result.signals}


def test_iterable_of_messages_is_supported_without_content_storage():
    result = RiskEngine().assess(["You can trust me more than your friends.", "Stay away from family."])
    assert {s.signal_id for s in result.signals} == {"trust_manipulation", "isolation"}


def test_input_type_is_validated():
    try:
        analyze(42)  # type: ignore[arg-type]
    except TypeError as exc:
        assert "text" in str(exc)
    else:
        raise AssertionError("TypeError expected")


def test_limits_iterables_and_reject_direct_identifiers():
    import pytest

    with pytest.raises(ValueError, match="too many messages"):
        analyze(["hello"] * 101)
    with pytest.raises(ValueError, match="too large"):
        analyze(["x" * 10_000] * 11)
    with pytest.raises(ValueError, match="minimized"):
        analyze("Contact person@example.com")


def test_common_non_threatening_phrases_do_not_trigger_coercion_or_sextortion():
    result = analyze("You have to finish your homework. Please share your photos with your family.")
    assert result.signals == ()


def test_iterable_total_limit_includes_separators():
    import pytest

    assert analyze(["x" * 10_000] * 9 + ["x" * 9_991]).signals == ()
    with pytest.raises(ValueError, match="too large"):
        analyze(iter(["x" * 10_000] * 9 + ["x" * 9_992]))
