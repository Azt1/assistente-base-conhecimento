import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from knowledge_assistant.api import create_app
from knowledge_assistant.gemini import Gemini
from knowledge_assistant.schemas import ChatResponse, SearchResponse


@pytest.mark.parametrize("path,schema", [
    ("/api/status", "StatusResponse"),
    ("/api/busca", "SearchResponse"),
    ("/api/chat", "ChatResponse"),
])
def test_documentacao_descreve_formato_de_saida(path, schema):
    document = TestClient(create_app(provider=Gemini("", ""))).get("/openapi.json").json()
    method = "get" if path == "/api/status" else "post"
    response = document["paths"][path][method]["responses"]["200"]
    assert response["content"]["application/json"]["schema"]["$ref"].endswith("/" + schema)


def test_fonte_sem_texto_nao_e_uma_resposta_valida():
    with pytest.raises(ValidationError):
        SearchResponse(fontes=[{"id": "entregas", "titulo": "Entregas"}])


def test_resposta_de_chat_exige_indicacao_de_resultado():
    with pytest.raises(ValidationError):
        ChatResponse(resposta="Texto", fontes=[])
