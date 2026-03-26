from ..models import ServerDefinition
from .builtin import BUILTIN_SERVERS, SERVERS_BY_NAME


class Registry:
    def __init__(self) -> None:
        self._servers = SERVERS_BY_NAME

    def get(self, name: str) -> ServerDefinition | None:
        return self._servers.get(name)

    def all(self) -> list[ServerDefinition]:
        return list(BUILTIN_SERVERS)

    def search(self, query: str) -> list[ServerDefinition]:
        if not query:
            return self.all()
        q = query.lower()
        results: list[ServerDefinition] = []
        for s in BUILTIN_SERVERS:
            haystack = " ".join([
                s.name, s.display_name, s.description,
                s.category, s.author, " ".join(s.tags),
            ]).lower()
            if q in haystack:
                results.append(s)
        return results

    def by_category(self, category: str) -> list[ServerDefinition]:
        return [s for s in BUILTIN_SERVERS if s.category == category]
