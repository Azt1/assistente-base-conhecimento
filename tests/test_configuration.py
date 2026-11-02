import pytest
from fastapi.testclient import TestClient

from knowledge_assistant.api import create_app
from knowledge_assistant.gemini import Gemini


@pytest.mark.parametrize("key,model", [("  ", "modelo-teste"), ("chave-ficticia", "  ")])
def test_espacos_nao_contam_como_configuracao(key, model):
    assert Gemini(key, model).configured is False


def test_remove_espacos_nas_pontas_das_variaveis():
    provider = Gemini("  chave-ficticia  ", " modelo-teste ")
    assert provider.configured is True
    assert provider.key == "chave-ficticia"
    assert provider.model == "modelo-teste"


def test_status_nao_retorna_valores_das_variaveis(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-ficticia")
    monkeypatch.setenv("GEMINI_MODEL", "modelo-teste")
    response = TestClient(create_app()).get("/api/status")
    assert response.json() == {"ia_configurada": True, "documentos": 3}
    assert "chave-ficticia" not in response.text
    assert "modelo-teste" not in response.text
