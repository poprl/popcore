from typing import Iterator, List
from .core import Player
from .population import Population
from .errors import POPULATION_PLAYER_NOT_EXIST


__all__ = [
    'flatten',
    'lineage',
    'generation'
]


def _get_player(population: Population, name: str = None) -> Player:
    """Returns the commit with the given name if it exists.

        Args:
            name (str): The name of the commit we are trying to get. If
                id_str is the empty string, returns the latest commit of the
                current branch. Defaults to the empty string.

        Raises:
            ValueError: If a commit with the specified `name` does not exist"""

    if name is None:
        return population._player

    if name not in population._objects:
        raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))

    return population.repo.commit(name)


def _get_players(population: Population, names: List[str]) -> List[Player]:
    """Returns the commit with the given id_str if it exists.

    Args:
        id_strs (List[str]): The id_str of the commits we are trying to
            get.

    Raises:
        KeyError: If a commit with one of the specified id_str does not
            exist
    """

    return [_get_player(population, name) for name in names]


def _get_ancesters(population: Population, name: str = None) -> List[str]:
    """Returns a list of all id_str of commits that came before the one
    with specified id_str.

    If id_str is not specified, it will return the commit history of the
    latest commit of the current branch.
    The list is of all commits that led to the specified commit. This
    means that commits from sister branches will not be included even if
    they may be more recent. However commits from ancestor branches would
    be included, up to _root.

    The list returned is in inverse chronological order, so the most
    recent commit appears first, and the oldest last."""

    player: None | Player = None

    if name is None:
        player = population._player
    else:
        if not population.repo.exists(name):
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))
        player = population.repo.commit(name)

    history = [player.id]
    player = player.parent
    while player is not None:
        history.append(player.id)
        player = player.parent

    return history


def _get_descendents(population: Population, name: str = None) -> List[str]:
    """Returns a list of all id_str of commits that came after the one
    with specified id_str, including branches.

    If id_str is not specified, it will default to the current commit.
    The list is of all commits that originate from the specified commit.

    The list returned is in no particular order."""

    player: None | Player  # Mypy cries if I don't specify that

    if name is None:
        player = population._player
    else:
        if not population.repo.exists(name):
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))
        player = population.repo.commit(name)

    history = [player.id]
    for player in player.descendants:
        history.extend(_get_descendents(population, player.id))

    return history


def lineage(population: Population, branch: str = None) -> Iterator[Player]:
    """Returns an iterator with the players in a given lineage (branch)

    Args:
        population (Population): The population to iterate over.

        branch (str): The name of the branch to iterate over. If None,
            iterate over the current branch. Defaults to None

    Returns:
        Iterator[Player]: An iterator over all commits in the given branch"""

    lineage = _get_ancesters(population, branch)[:-1]
    for player in _get_players(population, lineage):
        yield player


def generation(self, generation: int = -1) -> Iterator[Player]:
    """Returns an iterator with the players in the given generation

    Args:
        population (Population): The population to iterate over.

        gen (int): The generation to iterate over. Defaults to -1 (meaning the
            last generation).

    Returns:
        Iterator[Player]: An iterator over all commits in the given generation
    """

    raise NotImplementedError()


def flatten(population: Population) -> Iterator[Player]:
    """Returns an iterator with all the players in the population

    Args:
        population (Population): The population to iterate over.

    Returns:
        Iterator[Player]: An iterator over all commits in the given population
    """

    lineage = _get_descendents(population, population.head().id)[1:]
    for player in _get_players(population, lineage):
        yield player
