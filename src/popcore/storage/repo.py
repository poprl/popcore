from abc import abstractmethod
from dataclasses import dataclass
import os
from typing import Dict, Generic, List, Optional, TypeVar
import fsspec

from .keyvalue import KeyValueFile
from .core import Serializer, MultifileStore


Metadata = TypeVar("Metadata")


class Hook:
    """
       Hook
    """
    @abstractmethod
    def __call__(self, repo: 'Repository', metadata: Metadata, **kwds):
        raise NotImplementedError()


@dataclass
class RepositoryStructure:
    index: str | os.PathLike = 'index'
    branches: str | os.PathLike = 'branch'
    objects: str | os.PathLike = "objects"


class Repository(Generic[Metadata]):

    def __init__(
        self,
        stage: str = ".popcache",
        serializer: Optional[Serializer[Metadata, Dict]] = None,
        filesystem: 'Optional[str]' = 'file',
        filesystem_options: Optional[Dict] = None,
        pre_commit_hooks: Optional[List[Hook]] = None,
        post_commit_hooks: Optional[List[Hook]] = None,
    ) -> None:
        """
            TODO: Add documentation
        """
        self._stage = stage
        self._struct = RepositoryStructure()
        self._fs: fsspec.AbstractFileSystem = fsspec.filesystem(
            filesystem, storage_options=filesystem_options
        )
        self._metadata = MultifileStore(
            path=os.path.join(stage, 'meta'),
            filesystem=self._fs,
        )
        self._index = KeyValueFile(
            path=os.path.join(self._metadata.path, self._struct.index),
            filesystem=self._fs
        )
        self._metadata.write(self._struct.index, self._index)
        self._branches = KeyValueFile(
            path=os.path.join(self._metadata.path, self._struct.branches),
            filesystem=self._fs
        )
        self._metadata.write(self._struct.branches, self._branches)
        # binary objects store
        self._objects = KeyValueFile(
            path=os.path.join(self._metadata.path, self._struct.objects),
            filesystem=self._fs,
            serializer=serializer
        )
        self._metadata.write(self._struct.objects, self._objects)

        self._pre_hooks = pre_commit_hooks if pre_commit_hooks else []
        # Post-Commit Hooks
        self._post_hooks = post_commit_hooks if post_commit_hooks else []

    def commit(
        self, name: str, metadata: Optional[Metadata] = None,
        **kwargs
    ) -> str:
        if metadata is None:
            assert name in self._objects
            return self._objects.read(name)

        assert name not in self._index

        for hook in self._pre_hooks:
            hook(self, metadata, **kwargs)

        self._objects.write(metadata.id, metadata)
        self._index.write(metadata.id, metadata.id)
        # NOTE: generations do not match key-value
        # if player.generation not in self._gen:
        #     self._gen[player.generation] = []
        # self._gen[player.generation] += [player]

        for hook in self._post_hooks:
            hook(self, metadata, **kwargs)

        return metadata.id

    def branch(self, name: str, metadata: Optional[Metadata] = None) -> str:
        if metadata is None:
            assert name in self._branches
            return self._branches[name]

        # assert name not in self._branches
        self._branches.write(name, metadata.id)
        self._index.write(name, metadata.id)
        return name

    def exists(self, name: str):
        return name in self._index

    def remove(self):
        raise NotImplementedError()

    def delete(self):
        self._metadata.delete()
        self._fs.delete(self._stage, recursive=True)

    @property
    def structure(self):
        return self._struct
