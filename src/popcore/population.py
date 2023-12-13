from typing import Iterator, List, Optional, Set
from hashlib import sha1

from .errors import (
    POPULATION_COMMIT_EXIST, POPUPLATION_BRANCH_EXISTS,
    POPULATION_PLAYER_NOT_EXIST
)
from .core import Interaction, Player
from .storage.repo import Repository, Hook
from .storage.core import Serializer


class PlayerKeyValueSerializer(Serializer[Player, dict]):
    """A serializer that turns :class:`~popcore.core.Player` into dictionaries,
        and dictionaries of the right format into
        :class:`~popcore.core.Player`.

    :param List[str] exclude_fields: The fields to exclude during
        serialization. Defaults to ['descendants'].

    .. seealso::
        :class:`popcore.core.Player`
    """
    def __init__(
        self,
        exclude_fields: List[str] = ['descendants']
    ) -> None:
        super().__init__()
        self._exclude_fields = exclude_fields

    def serialize(self, player: Player) -> dict:
        """Creates a dictionary from the `player`, ignoring
            `self._exclude_fields`

        :param (Player) player: The player to turn into a dict.

        :return: A dictionary summarizing the player.
        :rtype: dict
        """
        fields = {
            k: v for k, v in player.__dict__.items()
            if k not in self._exclude_fields
        }
        fields['parent'] = player.parent.id if player.parent else None
        return fields

    def deserialize(self, key_value_store: dict) -> 'Player':
        """Turns a dictionary of the right format into a
            :class:`~popcore.core.Player`.

        :param dict key_value_store: The dictionary containing the player's
            parameters.

        :return: A player that corresponds to the dictionary passed.
        :rtype: Player
        """
        filtered = {
            k: v for k, v in key_value_store.items()
        }
        return Player(**filtered)


class PlayerAutoIdHook(Hook):
    """Hook to automatically assign IDs to players that don't have one.

    The ID is generated using cryptographic hashing.
    """
    def __call__(
        self, repo: Repository, player: Player,
        *args, **kwds
    ):
        """Automatically assign an ID to the player if it does not have one.

        :param Repository repo: _description_
        :param Player player: The player to automatically ID.
        """

        # TODO: repo unused, do we want to keep it as an arg?

        if player.id is not None:
            return player.id

        parent = player.parent
        path = parent.id + str(id(player))  # Avoid conflicts with siblings
        player.id = sha1(path.encode()).hexdigest()
        # player.path = f"{parent.path}/{player.id}"


class Population:
    """A data structure that records the evolution of populations of
    agents. It behaves like a git repository, where each branch is a
    unique agent and every commit corresponds to a specific iteration of
    said agent.

    This is initialized with a '_root' branch. Users should not commit
    directly to this branch if they want to track multiple separate agents,
    but rather create a branch for every new agent.

    :param Optional[Player] root: If not none, the specified player becomes
        the root of the population. Defaults to None.
    :param str root_name: The id of the root. Defaults to `'_root'`.
    :param str root_branch: The name of the root's branch.
        Defaults to `'main'`.
    :param Optional[Repository[Player]] stage: _description_. Defaults to
        `'.popcache'`.
    """

    def __init__(
        self,
        root: 'Optional[Player]' = None,
        root_name: str = "_root",
        root_branch: str = "main",
        stage: 'Optional[Repository[Player]]' = '.popcache',
    ):
        root = root if root else Player(
            parent=None, id=root_name, branch=root_branch
        )
        self._root = root

        self.repo = Repository[Player](
            stage=stage,
            pre_commit_hooks=[PlayerAutoIdHook()],
            serializer=PlayerKeyValueSerializer()
        )

        self.repo.commit(root_name, self._root)
        self.repo.branch(root_branch, self._root)

        # An array of every node indexed by generation (1st gen has index 0)
        # self._generations: List[List[Player]] = [[]]

        self._player: Player = self._root
        self._branch: str = self._root.branch

    def commit(
        self,
        id: str = None,
        interaction: "Interaction | None" = None,
        timestep: int = 1,
        **kwargs
    ) -> str:
        """Creates a new commit in the current branch.

        :param str id: A unique identifier for the commit (like the commit
            hash in git). Defaults to None
        :param Interaction interaction: The agents other than the parent that
            contributed to the last training step (opponents, allies,
            mates...). Defaults to None.
            TODO: update interaction description
        :param int timestep: The timestep when this commit was
            made. Defaults to 1.

        :raises ValueError: If a player with the specified id already exists

        :return: The id_str of the new commit.
        :rtype: str
        """
        # TODO: have pre_commit_hooks and post_commit_hooks as kwargs?
        if self.repo.exists(id):
            raise ValueError(POPULATION_COMMIT_EXIST.format(id))
        # Create the child node
        next_player = self._player.add_descendant(
            id=id,
            interaction=interaction,
            timestep=timestep,
            branch=self._branch
        )

        if self.repo.exists(next_player.id):
            raise ValueError(POPULATION_COMMIT_EXIST.format(id))

        self.repo.commit(next_player.id, next_player)
        self.repo.branch(self._branch, next_player)

        self._player = next_player

        return next_player.id

    def branch(self, name: str = None) -> str:
        """Create a new branch diverging from the current branch.

        :param str name: The name of the new branch. Must be unique.
            This will be a new alias to the current commit. If None, it
            returns the name of the active branch. Defaults to None.

        :raises ValueError: If a branch with the specified name/alias already
            exists

        :return: The name of the new commit
        :rtype: str

        .. seealso::
            :meth:`popcore.Population.branches`

            :meth:`popcore.Population.checkout`
        """

        if name is None:
            return self._branch

        if self.repo.exists(name):
            raise ValueError(POPUPLATION_BRANCH_EXISTS.format(name))

        self.repo.branch(name, self._player)

        return self.checkout(name)

    def checkout(self, name: str) -> str:
        """Set the current branch to the one specified.

        :param str name: The name of the branch or player to switch to.

        :raises ValueError: If there is no branch with the specified name

        :return: The name of the branch checked out
        :rtype: str

        .. seealso::
            :meth:`popcore.Population.branch`

            :meth:`popcore.Population.branches`
        """

        if not self.repo.exists(name):
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))

        if name in self.repo._branches:
            self._branch = name
            self._player: Player = self.repo.commit(
                self.repo.branch(name)
            )
        else:
            self._player: Player = self.repo.commit(name, None)
            self._branch = self._player.branch

        return self._branch

    def branches(self) -> Set[str]:
        """Returns a set of all branches.

        :rtype: Str[str]

        .. seealso::
            :meth:`popcore.Population.branch`

            :meth:`popcore.Population.checkout`
        """
        return set(self.repo._branches)

    def head(self) -> 'Player':
        """Return a reference to the current commit.

        :rtype: Player"""
        return self._player

    def detach(
        self,
    ) -> 'Population':
        """Creates a Population with the current commit as root.

        The new Population does not have any connection to the current one,
        hence this should be thread-safe. This may then be reattached once
        operations have been performed.

        :returns: A new population with the current commit as root.
        :rtype: Population

        .. seealso::
            :meth:`popcore.Population.attach`
        """
        # TODO: detach persistence. Plus this is broken
        detached_pop = Population(
            root=self._player,
            pre_commit_hooks=self._pre_commit_hooks,
            post_commit_hooks=self._post_commit_hooks,
            attach_hooks=self._attach_hooks,
        )
        return detached_pop

    def delete(self):
        self.repo.delete()
        self._player = None
        self._branch = None

    def __enter__(self):
        return self

    def __exit__(self, exctype, excinst, exctb) -> bool:
        self.delete()
        return False

    def attach(
        self,
        population: 'Population',
    ) -> None:
        """Merges back a previously detached population.

        Colliding branch names will have a number appended to fix the
        collision. Since commit id_str may collide, new hashes are made by
        default. The user may also provide an id_hook to control the way
        rehashing happens.

        Note that this function preforms changes on both populations involved
        in the operation, and that if one wishes to keep versions of these
        untouched, they should make a deepcopy beforehand.

        :param Population population: The population to merge in the current
            object. It's root's id_str should correspond to the id_str of
            an already existing node, which is where it will be attached.

        :raises ValueError: If the population's root's id_str does not match
            any current commit.
        :raises ValueError: If there is a collision between commit id_str.

        .. seealso::
            :meth:`popcore.Population.detach`
        """

        # TODO Warning: If a model is saved in a detached pop, and the pop is
        # then reattached, the re-hashing of the commits might make the model
        # not loadable anymore since the name changed

        # TODO: attach persistence
        if population._root.id not in self.repo:
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(
                population._root.id))

        # Pick the right place to reattach
        node: Player = self.repo[population._root.id]

        # Transfer all the nodes from the other pop to the right place
        for player in population._root.descendants:
            node.descendants.append(player)
            player.parent = node

        nodes_to_add = {}

        # Rename branches in attached pop to avoid conflicts
        branches_to_add, branch_renaming = self._rename_conflicting_branches(
            population
        )

        for name, player in population.repo.items():
            # Ignore root node
            if name == population._root.id:
                continue

            # Add the renamed branches to the main pop
            if name in population._branches:
                nodes_to_add[branch_renaming[name]] = player
                continue

            # Apply branch renaming
            player.branch = branch_renaming[player.branch]

            player.generation += node.generation

            if player.name is None:
                # TODO: This seems incomplete
                node = player
                path = ''
                while node is not None:
                    path += str(node)
                    node = node.parent

            if name in self.repo:
                raise ValueError(POPULATION_COMMIT_EXIST.format(name))

            # Add player to the index
            self._nodes[player.name] = player

            self._add_gen(player)

        # Add branches to the index
        self._nodes.update(nodes_to_add)
        self._branches = self._branches.union(branches_to_add)

    def lineage(self, branch: str = None) -> Iterator[Player]:
        """Returns an iterator over all the commits in the given lineage
        (branch).

        :param Population population: The population to iterate over.

        :param str branch: The name of the branch to iterate over. If None,
            iterate over the current branch. Defaults to None

        :return: An iterator over all commits in the given branch
        :rtype: Iterator[Player]

        .. seealso::
            :meth:`popcore.population.Population.generation`

            :meth:`popcore.population.Population.flatten`
        """

        lineage = self._get_ancesters(branch)[:-1]
        for player in self._get_players(lineage):
            yield player

    def generation(self, generation: int = -1) -> Iterator[Player]:
        """Returns an iterator over the commits in the given generation.

        :param Population population: The population to iterate over.

        :param int gen: The generation to iterate over. Defaults to -1
            (meaning the last generation).

        :retun: An iterator over all commits in the given generation
        :rtype: Iterator[Player]

        .. seealso::
            :meth:`popcore.population.Population.lineage`

            :meth:`popcore.population.Population.flatten`
        """

        raise NotImplementedError()

    def flatten(self) -> Iterator[Player]:
        """Returns an iterator over all the commits in the population.

        :param Population population: The population to iterate over.

        :return: An iterator over all commits in the given population
        :rtype: Iterator[Player]

        .. seealso::
            :meth:`popcore.population.Population.lineage`

            :meth:`popcore.population.Population.generation`
        """

        lineage = self._get_descendents(self._root.id)[1:]
        for player in self._get_players(lineage):
            yield player

    @property
    def stage(self):
        return self.repo._stage

    def _rename_conflicting_branches(self, population: 'Population'):
        """Every branch that generates a conflict gets renamed by adding an
        integer at the end"""

        branches_to_add = set()
        branch_renaming = {}

        for branch in population._branches:
            new_branch = branch
            i = 1
            while self._index.exists(new_branch):
                new_branch = branch + str(i)
                i += 1

            branches_to_add.add(new_branch)
            branch_renaming[branch] = new_branch

        return branches_to_add, branch_renaming

    def _get_player(self, name: str = None) -> Player:
        """Returns the commit with the given id_str if it exists.

        Args:
            name (str): The name of the commit we are trying to get. If
                id_str is the empty string, returns the latest commit of
                the current branch. Defaults to the empty string.

        Raises:
            ValueError: If a commit with the specified `name` does not
            exist
        """

        if name is None:
            return self._player

        if name not in self._objects:
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))

        return self.repo.commit(name)

    def _get_players(self, names: List[str]) -> List[Player]:
        """Returns the commit with the given id_str if it exists.

        Args:
            id_strs (List[str]): The id_str of the commits we are trying to
                get.

        Raises:
            KeyError: If a commit with one of the specified id_str does not
                exist
        """

        return [self._get_player(name) for name in names]

    def _get_ancesters(self, name: str = None) -> List[str]:
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

        player: None | Player  # Mypy cries if I don't specify that

        if name is None:
            player = self._player
        else:
            if not self.repo.exists(name):
                raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))
            player = self.repo.commit(name)

        history = [player.id]
        player = player.parent
        while player is not None:
            history.append(player.id)
            player = player.parent

        return history

    def _get_descendents(self, name: str = None) -> List[str]:
        """Returns a list of all id_str of commits that came after the one
        with specified id_str, including branches.

        If id_str is not specified, it will default to the current commit.
        The list is of all commits that originate from the specified commit.

        The list returned is in no particular order."""

        player: None | Player  # Mypy cries if I don't specify that

        if name is None:
            player = self._player
        else:
            if not self.repo.exists(name):
                raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))
            player = self.repo.commit(name)

        history = [player.id]
        for player in player.descendants:
            history.extend(self._get_descendents(player.id))

        return history
