import pytest
from fastapi.testclient import TestClient

from knowledge_assistant.api import create_app
from knowledge_assistant.gemini import Gemini


@pytest.fixture
def client():
    return TestClient(create_app(provider=Gemini("", "")))


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_limita_documentos_com_ordem_estavel(client, limit):
    response = client.post("/api/busca", json={"pergunta": "Loja Aurora", "limite": limit})
    assert response.status_code == 200
    sources = response.json()["fontes"]
    assert len(sources) == limit
    assert [source["id"] for source in sources] == ["atendimento", "entregas", "trocas"][:limit]


def test_omitir_limite_mantem_tres_resultados(client):
    response = client.post("/api/busca", json={"pergunta": "Loja Aurora"})
    assert len(response.json()["fontes"]) == 3


@pytest.mark.parametrize("limit", [0, -1, 4, 1.5, "2", True, None])
def test_rejeita_limite_fora_do_contrato(client, limit):
    response = client.post("/api/busca", json={"pergunta": "Loja Aurora", "limite": limit})
    assert response.status_code == 422


def test_limite_nao_cria_resultados_sem_correspondencia(client):
    response = client.post("/api/busca", json={"pergunta": "astronomia", "limite": 1})
    assert response.status_code == 200
    assert response.json() == {"fontes": []}
