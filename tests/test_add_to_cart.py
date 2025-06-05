import types
from unittest.mock import MagicMock

import flask_login
import pytest

import importlib.util

spec = importlib.util.spec_from_file_location("app", "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    return app.app.test_client()

def _mock_db():
    """Return a mock DB connection with cursor context."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn, mock_cursor


def _login(monkeypatch, user_id=1):
    dummy_user = types.SimpleNamespace(id=user_id, is_authenticated=True)
    monkeypatch.setattr(flask_login.utils, '_get_user', lambda: dummy_user)


def test_add_to_cart_valid_quantity(client, monkeypatch):
    mock_conn, mock_cursor = _mock_db()
    monkeypatch.setattr(app, 'get_db_connection', lambda: mock_conn)
    _login(monkeypatch)

    resp = client.post('/add_to_cart/1', data={'quantity': '2'})
    assert resp.status_code == 302
    assert mock_cursor.execute.called
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
    assert ('success', '已添加到购物车。') in flashes


@pytest.mark.parametrize('qty', ['0', '-1', 'abc'])
def test_add_to_cart_invalid_quantity(client, monkeypatch, qty):
    mock_conn, mock_cursor = _mock_db()
    monkeypatch.setattr(app, 'get_db_connection', lambda: mock_conn)
    _login(monkeypatch)

    resp = client.post('/add_to_cart/1', data={'quantity': qty})
    assert resp.status_code == 302
    # Should not perform DB operations
    assert not mock_cursor.execute.called
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
    assert ('danger', '无效的数量。') in flashes
