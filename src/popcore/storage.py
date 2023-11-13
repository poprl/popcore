from abc import ABC, abstractmethod
from typing import List

from popcore import Player
from . import Population, Player


class Index(ABC):

    @abstractmethod
    def save(self, name: str, player: Player) -> str:
        raise NotImplementedError()

    @abstractmethod
    def load(self, name: str) -> Player:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, name: str) -> bool:
        raise NotImplementedError()


class MemoryIndex(Index):

    def __init__(self) -> None:
        self._nodes: dict[str, Player] = dict()
        self._generations: List[List[Player]] = []

    def save(self, name: str, player: Player) -> str:
        assert name not in self._nodes
        self._nodes[name] = player

        if len(self._generations) <= player.generation:
            self._generations.append([])
        self._generations[player.generation].append(player)

        return player.name

    def exists(self, name: str) -> bool:
        return name in self._nodes


class LocalIndex(Index):

    def __init__(self) -> None:
        self._cache = MemoryIndex()
