import pytest
from fastapi.testclient import TestClient

from knowledge_assistant.api import UNKNOWN, create_app
from knowledge_assistant.gemini import ModelAnswer


class LocalProvider:
    """Resposta controlada apenas para testes, sem acesso ao modelo ou à rede."""

    configured = True

    def __init__(self, answer):
        self.result = answer
        self.calls = []

    def answer(self, question, sources):
        self.calls.append((question, sources))
        return self.result


def ask(client, question="prazo entrega"):
    return client.post("/api/chat", json={"pergunta": question, "autoriza_envio": True})


def test_retorna_texto_e_fonte_original():
    provider = LocalProvider(ModelAnswer(resposta="Prazo de 5 a 8 dias úteis.", fontes=["entregas"], encontrou=True))
    response = ask(TestClient(create_app(provider=provider)))
    assert response.status_code == 200
    data = response.json()
    assert data["encontrou"] is True
    assert data["resposta"] == provider.result.resposta
    assert data["fontes"][0]["id"] == "entregas"
    assert "5 a 8 dias úteis" in data["fontes"][0]["texto"]
    assert provider.calls[0][0] == "prazo entrega"
    assert [source.id for source in provider.calls[0][1]] == ["entregas"]


def test_nao_repete_mesma_fonte():
    provider = LocalProvider(ModelAnswer(resposta="Resposta de teste.", fontes=["entregas", "entregas"], encontrou=True))
    assert len(ask(TestClient(create_app(provider=provider))).json()["fontes"]) == 1


@pytest.mark.parametrize("sources", [[], ["inventada"], ["trocas"], ["entregas", "inventada"]])
def test_recusa_resposta_sem_fonte_ou_com_fonte_nao_enviada(sources):
    provider = LocalProvider(ModelAnswer(resposta="Não deve ser exibida.", fontes=sources, encontrou=True))
    response = ask(TestClient(create_app(provider=provider)))
    assert response.status_code == 200
    assert response.json() == {"resposta": UNKNOWN, "fontes": [], "encontrou": False}


def test_modelo_pode_indicar_falta_de_informacao():
    provider = LocalProvider(ModelAnswer(resposta="Sem informação.", fontes=[], encontrou=False))
    assert ask(TestClient(create_app(provider=provider))).json()["resposta"] == UNKNOWN


def test_sem_documentos_relacionados_nao_chama_modelo():
    provider = LocalProvider(ModelAnswer(resposta="Não utilizada.", fontes=[], encontrou=False))
    result = ask(TestClient(create_app(provider=provider)), "astronomia")
    assert result.json()["encontrou"] is False
    assert provider.calls == []


def test_sem_autorizacao_nao_chama_modelo():
    provider = LocalProvider(ModelAnswer(resposta="Não utilizada.", fontes=[], encontrou=False))
    response = TestClient(create_app(provider=provider)).post("/api/chat", json={"pergunta": "prazo entrega"})
    assert response.status_code == 400
    assert provider.calls == []
