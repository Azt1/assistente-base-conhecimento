from fastapi.testclient import TestClient

from knowledge_assistant.api import create_app
from knowledge_assistant.gemini import ModelAnswer, ProviderError


class FailingProvider:
    configured = True

    def __init__(self):
        self.calls = 0

    def answer(self, question, sources):
        self.calls += 1
        if self.calls <= 3:
            raise ProviderError("Detalhe interno que não deve chegar ao usuário.")
        return ModelAnswer(resposta="Resposta de teste.", fontes=["entregas"], encontrou=True)


def test_erro_do_provedor_tem_mensagem_publica_sem_detalhes_internos():
    client = TestClient(create_app(provider=FailingProvider()))
    response = client.post("/api/chat", json={"pergunta": "prazo entrega", "autoriza_envio": True})
    assert response.status_code == 502
    assert response.json() == {"detail": "A IA não conseguiu responder agora. Tente novamente em instantes."}
    assert "Detalhe interno" not in response.text


def test_falhas_liberam_vagas_para_novas_consultas():
    provider = FailingProvider()
    client = TestClient(create_app(provider=provider))
    for _ in range(3):
        response = client.post("/api/chat", json={"pergunta": "prazo entrega", "autoriza_envio": True})
        assert response.status_code == 502
    response = client.post("/api/chat", json={"pergunta": "prazo entrega", "autoriza_envio": True})
    assert response.status_code == 200
    assert response.json()["encontrou"] is True
    assert provider.calls == 4
