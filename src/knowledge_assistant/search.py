from dataclasses import dataclass, asdict
from pathlib import Path
import re
import unicodedata

STOPWORDS = set("a o as os de do da dos das em no na nos nas para por e com um uma qual quais que como quando quanto quantos posso sao ser tem meu minha voces se eu".split())


def tokens(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return set(re.findall(r"[a-z0-9]+", text)) - STOPWORDS


@dataclass(frozen=True)
class Source:
    id: str
    titulo: str
    texto: str

    def to_dict(self):
        return asdict(self)


class KnowledgeBase:
    def __init__(self, directory: Path):
        self.sources = []
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            self.sources.append(Source(path.stem, text.splitlines()[0].lstrip("# "), text))

    def search(self, question: str, limit: int = 3) -> list[Source]:
        query = tokens(question)
        ranked = []
        for source in self.sources:
            words = tokens(source.texto)
            common = query & words
            if common:
                ranked.append((len(common) / max(len(query), 1), source))
        ranked.sort(key=lambda item: (-item[0], item[1].id))
        return [source for _, source in ranked[:limit]]
