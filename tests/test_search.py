from pathlib import Path

import pytest

from knowledge_assistant.search import KnowledgeBase, tokens


@pytest.fixture
def base(tmp_path):
    (tmp_path / "entregas.md").write_text("# Entregas\nPrazo de entrega: 5 dias úteis.", encoding="utf-8")
    (tmp_path / "trocas.md").write_text("# Trocas\nTrocas de produtos em 7 dias.", encoding="utf-8")
    return KnowledgeBase(tmp_path)


def test_normaliza_acentos_e_maiusculas():
    assert tokens("QUAL o PRAZO em dias ÚTEIS?") == {"prazo", "dias", "uteis"}


def test_documento_mais_relacionado_vem_primeiro(base):
    result = base.search("prazo entrega dias")
    assert result[0].id == "entregas"
    assert result[0].titulo == "Entregas"
    assert "5 dias" in result[0].texto


def test_sem_palavras_relacionadas_nao_retorna_fontes(base):
    assert base.search("astronomia") == []


def test_apenas_palavras_comuns_nao_retorna_fontes(base):
    assert base.search("qual o de") == []


def test_respeita_limite(base):
    assert len(base.search("dias", limit=1)) == 1


@pytest.mark.parametrize("limit", [0, -1])
def test_rejeita_limite_invalido(base, limit):
    with pytest.raises(ValueError, match="limite"):
        base.search("dias", limit=limit)


def test_ignora_arquivo_vazio_e_outras_extensoes(tmp_path):
    (tmp_path / "vazio.md").write_text(" \n", encoding="utf-8")
    (tmp_path / "texto.txt").write_text("Prazo de entrega", encoding="utf-8")
    assert KnowledgeBase(tmp_path).sources == []


def test_pasta_vazia_nao_tem_resultados(tmp_path):
    assert KnowledgeBase(tmp_path).search("entrega") == []


def test_pasta_inexistente_tem_erro_claro(tmp_path):
    with pytest.raises(ValueError, match="pasta"):
        KnowledgeBase(tmp_path / "inexistente")


def test_empate_tem_ordem_estavel(base):
    assert [item.id for item in base.search("dias")] == ["entregas", "trocas"]
