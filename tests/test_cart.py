import types
import pytest
import app as app_module

class DummyUser:
    def __init__(self, user_id=1):
        self.id = user_id
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False


def test_calculate_cart_total(monkeypatch):
    def fake_get_cart_items(user_id):
        return [
            {"price": 10.0, "quantity": 2},
            {"price": 5.0, "quantity": 3},
        ]

    monkeypatch.setattr(app_module, "get_cart_items", fake_get_cart_items)
    assert app_module.calculate_cart_total(1) == 10.0 * 2 + 5.0 * 3


def test_add_to_cart_invalid_quantity(monkeypatch):
    calls = {}

    def fake_flash(msg, category):
        calls["flash"] = msg

    monkeypatch.setattr(app_module, "flash", fake_flash)

    def fake_get_db_connection():
        calls["db"] = True

    monkeypatch.setattr(app_module, "get_db_connection", fake_get_db_connection)
    monkeypatch.setattr(app_module, "current_user", DummyUser())

    with app_module.app.test_request_context(
        "/add_to_cart/1", method="POST", data={"quantity": "-1"}
    ):
        resp = app_module.add_to_cart.__wrapped__(1)

    assert resp.status_code == 302
    assert "数量必须为正整数" in calls["flash"]
    assert "db" not in calls
