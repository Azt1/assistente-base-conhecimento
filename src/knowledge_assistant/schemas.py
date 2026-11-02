from pydantic import BaseModel


class SourceResponse(BaseModel):
    id: str
    titulo: str
    texto: str


class SearchResponse(BaseModel):
    fontes: list[SourceResponse]


class ChatResponse(SearchResponse):
    resposta: str
    encontrou: bool


class StatusResponse(BaseModel):
    ia_configurada: bool
    documentos: int
