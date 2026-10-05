from tools.mail_guard import decide

ME = "joaco@example.com"


def test_email_only_to_himself_is_allowed():
    assert decide({"to": ["Joaco@Example.com"], "subject": "Reporte"}, ME) == "allow"


def test_any_other_recipient_is_left_to_ask():
    assert decide({"to": [ME, "rrhh@banco.com"]}, ME) is None
    assert decide({"to": [ME], "cc": ["alguien@x.com"]}, ME) is None
    assert decide({"to": [ME], "bcc": ["alguien@x.com"]}, ME) is None


def test_missing_recipients_or_unset_address_is_left_to_ask():
    assert decide({"subject": "sin destinatario"}, ME) is None
    assert decide({"to": [ME]}, None) is None


def test_a_single_string_recipient_is_understood():
    assert decide({"to": ME}, ME) == "allow"
