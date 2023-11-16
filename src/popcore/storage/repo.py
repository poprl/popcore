from dataclasses import dataclass
import os
from typing import Dict, Optional

from .keyvalue import KeyValueFileStore
from .binary import BinaryFileStore
from ..core import Player


@dataclass
class RepositoryStructure:
    index: str | os.PathLike = 'index'
    gen: str | os.PathLike = 'gen'
    branches: str | os.PathLike = 'branch'
    objects: str | os.PathLike = 'objects/'


class Repository:

    def __init__(
        self,
        stage: str = ".popcore",
        filesystem: 'Optional[str]' = 'file',
        filesystem_options: Optional[Dict] = None,
    ) -> None:
        """
            TODO: Add documentation
        """

        self._struct = RepositoryStructure()

        self._metadata = KeyValueFileStore(
            path=stage,
            filesystem=filesystem,
            filesystem_options=filesystem_options
        )
        self._metadata['index'] = self._struct.index
        self._metadata["branches"] = self._struct.branches
        self._metadata["gen"] = self._struct.gen

        self._index = self._metadata["index"]
        self._branches = self._metadata["branches"]
        self._gen = self._metadata["gen"]
        self._objects = BinaryFileStore(
            path=os.path.join(stage, self._struct.objects),
            filesystem=filesystem,
            filesystem_options=filesystem_options,
        )

    def commit(self, name: str, player: 'Player') -> str:
        assert name not in self._index
        self._index[name] = player
        # NOTE: generations do not match key-value
        if player.generation not in self._gen:
            self._gen[player.generation] = []
        self._gen[player.generation] += [player]

        return player.name

    def checkout(self, name):
        assert name in self._index
        return self._index[name]

    def verify(self, name: str):
        return name in self._index

    def branch(self, name: str, player: 'Player'):
        assert name not in self._branches
        self._branches[name] = player.name

        return name

    def remove(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    @property
    def structure(self):
        return self._struct
