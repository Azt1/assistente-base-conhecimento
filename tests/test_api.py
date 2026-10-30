import pytest
from fastapi.testclient import TestClient

from knowledge_assistant.api import create_app
from knowledge_assistant.gemini import Gemini


@pytest.fixture
def client():
    return TestClient(create_app(provider=Gemini("", "")))


def test_status_nao_expoe_chave(client):
    assert client.get("/api/status").json() == {"ia_configurada": False, "documentos": 3}


def test_documentacao_disponivel(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/").json()["documentacao"] == "/docs"


def test_busca_retorna_fonte_original(client):
    response = client.post("/api/busca", json={"pergunta": "prazo entrega"})
    assert response.status_code == 200
    source = response.json()["fontes"][0]
    assert source["id"] == "entregas"
    assert "5 a 8 dias úteis" in source["texto"]


def test_sem_resultado_retorna_lista_vazia(client):
    response = client.post("/api/busca", json={"pergunta": "astronomia"})
    assert response.status_code == 200
    assert response.json() == {"fontes": []}


@pytest.mark.parametrize("question", ["", "   ", "a", "a" * 501, None, 123])
def test_rejeita_perguntas_invalidas(client, question):
    assert client.post("/api/busca", json={"pergunta": question}).status_code == 422


def test_pergunta_obrigatoria(client):
    assert client.post("/api/busca", json={}).status_code == 422


def test_chat_exige_autorizacao(client):
    response = client.post("/api/chat", json={"pergunta": "prazo entrega"})
    assert response.status_code == 400
    assert "Autorize" in response.json()["detail"]


def test_chat_sem_chave_nao_finge_resposta(client):
    response = client.post("/api/chat", json={"pergunta": "prazo entrega", "autoriza_envio": True})
    assert response.status_code == 503
    assert "não está configurada" in response.json()["detail"]
