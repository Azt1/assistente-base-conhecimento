import json

import httpx
import pytest

from knowledge_assistant.gemini import Gemini, ProviderError
from knowledge_assistant.search import Source


SOURCE = Source("entregas", "Entregas", "O prazo é de 5 a 8 dias úteis.")
ANSWER = {"resposta": "O prazo é de 5 a 8 dias úteis.", "fontes": ["entregas"], "encontrou": True}


def envelope(answer):
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(answer)}]}}]}


def test_monta_requisicao_e_le_resposta_sem_acessar_rede():
    def handler(request):
        assert request.method == "POST"
        assert request.url.host == "generativelanguage.googleapis.com"
        assert request.url.path.endswith("/models/modelo-teste:generateContent")
        assert request.headers["x-goog-api-key"] == "chave-ficticia"
        assert "chave-ficticia" not in str(request.url)
        body = json.loads(request.content)
        context = json.loads(body["contents"][0]["parts"][0]["text"])
        assert context == {"pergunta": "Qual o prazo?", "fontes": [SOURCE.to_dict()]}
        assert body["systemInstruction"]["parts"][0]["text"]
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        return httpx.Response(200, json=envelope(ANSWER))

    provider = Gemini("chave-ficticia", "modelo-teste", transport=httpx.MockTransport(handler))
    result = provider.answer("Qual o prazo?", [SOURCE])
    assert result.resposta == ANSWER["resposta"]
    assert result.fontes == ["entregas"]
    assert result.encontrou is True


@pytest.mark.parametrize("key,model", [("", "modelo"), ("chave-ficticia", ""), ("chave-ficticia", "../modelo")])
def test_configuracao_invalida_nao_envia_requisicao(key, model):
    def handler(request):
        pytest.fail("Não deve fazer requisição sem configuração válida.")

    with pytest.raises(ProviderError, match="Configure"):
        Gemini(key, model, httpx.MockTransport(handler)).answer("Prazo?", [SOURCE])


@pytest.mark.parametrize("body", [
    {}, {"candidates": []}, {"candidates": [None]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": [None]}}]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": "texto"}}]},
    envelope({"resposta": "   ", "fontes": ["entregas"], "encontrou": True}),
    envelope({"resposta": "Resposta", "fontes": "entregas", "encontrou": True}),
    envelope({"resposta": "Resposta", "fontes": [], "encontrou": "true"}),
])
def test_resposta_fora_do_formato_tem_erro_controlado(body):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    with pytest.raises(ProviderError, match="resposta válida"):
        Gemini("chave-ficticia", "modelo-teste", transport).answer("Prazo?", [SOURCE])


@pytest.mark.parametrize("reason", ["SAFETY", "MAX_TOKENS"])
def test_nao_utiliza_resposta_bloqueada_ou_incompleta(reason):
    body = envelope(ANSWER)
    body["candidates"][0]["finishReason"] = reason
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    with pytest.raises(ProviderError, match="não concluiu"):
        Gemini("chave-ficticia", "modelo-teste", transport).answer("Prazo?", [SOURCE])


@pytest.mark.parametrize("status", [401, 429, 500])
def test_erro_http_nao_expoe_corpo_do_provedor(status):
    transport = httpx.MockTransport(lambda request: httpx.Response(status, text="detalhe privado"))
    with pytest.raises(ProviderError) as result:
        Gemini("chave-ficticia", "modelo-teste", transport).answer("Prazo?", [SOURCE])
    assert "detalhe privado" not in str(result.value)
    assert "chave-ficticia" not in str(result.value)


def test_timeout_tem_erro_controlado():
    def handler(request):
        raise httpx.ReadTimeout("Tempo esgotado", request=request)

    with pytest.raises(ProviderError, match="resposta válida"):
        Gemini("chave-ficticia", "modelo-teste", httpx.MockTransport(handler)).answer("Prazo?", [SOURCE])


def test_json_malformado_tem_erro_controlado():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="não é JSON"))
    with pytest.raises(ProviderError, match="resposta válida"):
        Gemini("chave-ficticia", "modelo-teste", transport).answer("Prazo?", [SOURCE])
