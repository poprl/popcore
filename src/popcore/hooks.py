
from abc import abstractmethod
from typing import Any
from hashlib import sha1

import popcore as core


class Hook:
    """
       Hook
    """
    @abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError()


class PreCommitHook(Hook):
    """
        PreCommitHook
    """
    @abstractmethod
    def _pre(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ):
        raise NotImplementedError()

    def __call__(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ) -> Any:
        return self._pre(population, player, args=args, kwds=kwds)


class PostCommitHook(Hook):
    """
       PostCommitHook
    """
    @abstractmethod
    def _post(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ):
        raise NotImplementedError()

    def __call__(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ) -> Any:
        return self._post(population, player, args=args, kwds=kwds)


class AttachHook(Hook):
    """
       AttachHook
    """
    @abstractmethod
    def _attach(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ):
        raise NotImplementedError()

    def __call__(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ) -> Any:
        return self._attach(population, player, args=args, kwds=kwds)


class AutoIdHook(PreCommitHook):

    def _pre(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ):
        if player.name is not None:
            return player.name

        parent = player.parent
        path = parent.path + str(id(player))  # Avoid conflicts with siblings
        player.name = sha1(path.encode()).hexdigest()
        player.path = f"{parent.path}/{player.name}"


class ReIdHook(AttachHook):

    def _attach(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ):
        if player.name is not None:
            return player.name

        # TODO: This seems incomplete
        node = player
        path = ''
        while node is not None:
            path += str(node)
            node = node.parent


class StorageHook(PostCommitHook):

    def __init__(self) -> None:
        super().__init__()

    def _post(
        self, population: 'core.Population', player: 'core.Player',
        *args: Any, **kwds: Any
    ):
        return super()._post(population, player, *args, **kwds)
