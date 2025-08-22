import json
from src.i18n.translations import translations


def test_i18n_has_required_keys():
    keys = [
        "menu.main.title",
        "subscriptions.list.title",
        "payment.waiting.title",
        "payment.success.title",
    ]
    for lang in ["ru", "en"]:
        for key in keys:
            text = translations.get(key, lang)
            assert isinstance(text, str) and text != key


def test_i18n_placeholders_substitution():
    ru = translations.get("payment.success.title", "ru", until_date="2025-01-01")
    en = translations.get("payment.success.title", "en", until_date="2025-01-01")
    assert "2025-01-01" in ru
    assert "2025-01-01" in en

