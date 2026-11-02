import os
from pathlib import Path
from threading import BoundedSemaphore

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from .gemini import Gemini, ProviderError
from .search import KnowledgeBase
from .schemas import ChatResponse, SearchResponse, StatusResponse

ROOT = Path(__file__).parent
UNKNOWN = "Não encontrei informação suficiente na base. Procure o atendimento humano."


class Question(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500)

    @field_validator("pergunta")
    @classmethod
    def clean(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Escreva uma pergunta com pelo menos 3 caracteres.")
        return value


class ChatQuestion(Question):
    autoriza_envio: bool = False


def create_app(provider=None, base=None):
    app = FastAPI(title="Assistente da base de conhecimento", version="0.1.0")
    knowledge = base if base is not None else KnowledgeBase(ROOT / "base")
    model = provider if provider is not None else Gemini(os.getenv("GEMINI_API_KEY", ""), os.getenv("GEMINI_MODEL", ""))
    slots = BoundedSemaphore(2)

    @app.get("/")
    def home():
        return {"projeto": "Assistente da base de conhecimento", "documentacao": "/docs"}

    @app.get("/api/status", response_model=StatusResponse)
    def status():
        return {"ia_configurada": model.configured, "documentos": len(knowledge.sources)}

    @app.post("/api/busca", response_model=SearchResponse)
    def search(question: Question):
        return {"fontes": [source.to_dict() for source in knowledge.search(question.pergunta)]}

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(question: ChatQuestion):
        if not question.autoriza_envio:
            raise HTTPException(400, "Autorize o envio da pergunta e dos trechos ao provedor de IA.")
        if not model.configured:
            raise HTTPException(503, "A IA ainda não está configurada. Use a busca local ou configure as variáveis no servidor.")
        sources = knowledge.search(question.pergunta)
        if not sources:
            return {"resposta": UNKNOWN, "fontes": [], "encontrou": False}
        if not slots.acquire(blocking=False):
            raise HTTPException(429, "Há duas consultas em andamento. Tente novamente em instantes.")
        try:
            result = model.answer(question.pergunta, sources)
        except ProviderError as error:
            raise HTTPException(502, str(error)) from error
        finally:
            slots.release()
        allowed = {source.id: source for source in sources}
        if not result.encontrou or not result.fontes or any(identifier not in allowed for identifier in result.fontes):
            return {"resposta": UNKNOWN, "fontes": [], "encontrou": False}
        citations = [allowed[identifier].to_dict() for identifier in dict.fromkeys(result.fontes)]
        return {"resposta": result.resposta, "fontes": citations, "encontrou": True}

    return app


app = create_app()
