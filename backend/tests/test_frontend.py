from fastapi.testclient import TestClient


def test_raiz_serve_o_index(client: TestClient) -> None:
    # a fixture `client` já monta o front (create_app monta frontend/ se a pasta existe)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Hamburgueria" in resp.text
    assert "app.js" in resp.text
