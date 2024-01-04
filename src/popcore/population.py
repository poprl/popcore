from dataclasses import dataclass
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

    def __init__(
        self,
        exclude_fields: List[str] = ['descendants']
    ) -> None:
        super().__init__()
        self._exclude_fields = exclude_fields

    def serialize(self, player: Player) -> dict:
        fields = {
            k: v for k, v in player.__dict__.items()
            if k not in self._exclude_fields
        }
        fields['parent'] = player.parent.id if player.parent else None
        return fields

    def deserialize(self, key_value_store: dict) -> 'Player':
        filtered = {
            k: v for k, v in key_value_store.items()
        }
        return Player(**filtered)


class PlayerAutoIdHook(Hook):

    def __call__(
        self, repo: Repository, player: Player,
        *args, **kwds
    ):
        if player.id is not None:
            return player.id

        parent = player.parent
        path = parent.id + str(id(player))  # Avoid conflicts with siblings
        player.id = sha1(path.encode()).hexdigest()
        # player.path = f"{parent.path}/{player.id}"


@dataclass
class MetaNode:
    player: Player
    parent: 'MetaNode'
    descendants: List['MetaNode']
    interaction: Optional[Interaction] = None
    generation: Optional[int] = 0
    timestep: Optional[int] = 1
    branch: Optional[str] = 0
    id: str = None

    def __post_init__(self):
        if self.player is not None:
            self.id = self.player.id

    def add_descendant(
        self,
        player: Player,
        interaction: Optional['Interaction'] = None,
        timestep: Optional[int] = 1,
        branch: Optional[str] = None
    ) -> 'Player':

        """Adds a decendant to this node

        If `node` is directly specified then it will be added as a child.
        Otherwise, the other parameters will be used to create a new node
        and add it as a child.

        Args:
            model_parameters (Any): The model parameters of the child to be
                added. Defaults to None.
            id_str (str): The id_str of the child. If this is the empty string,
                a unique id_str will be picked at random.
                Defaults to the empty string.
            hyperparameters (Dict[str, Any]): A dictionary of the
                hyperparameters that define the transition from this node
                to the new child. This should contain enough information to
                reproduce the evolution step deterministically given the
                parent and contributors parameters.
                Defaults to an empty dict.
            interaction (List[Player]): All the models
                other than the parent that contributed to the evolution.
                Typically, that would be opponents and allies, or mates in
                the case of genetic crossover.
                For example, if the model played a game of chess against
                an opponent and learned from it, the parent would be the
                model before that game, and the contributor would be the
                opponent. Defaults to an empty list.

        Returns:
            Player: The new descendant

        """

        branch = self.branch if branch is None else branch

        # Create child node
        descendant = MetaNode(
            player=player,
            parent=self,
            interaction=interaction,
            generation=self.generation + 1,
            timestep=timestep,
            branch=branch
        )

        self.descendants.append(descendant)

        return descendant


class Population:
    """A data structure to manipulate evolving populations of players.
    The structure is meant to be similar to that of a git repository, where
    every commit corresponds to an agent."""

    def __init__(
        self,
        root: Optional[MetaNode] = None,
        root_name: str = "_root",
        root_branch: str = "main",
        stage: 'Optional[Repository[MetaNode]]' = '.popcache',
    ):
        """Instantiates population of players.

        This is a data structure that records the evolution of populations of
        agents. It behaves like a git repository, where each branch is a
        unique agent and every commit corresponds to a specific iteration of
        said agent.

        This is initialized with a '_root' branch. Users should not commit
        directly to this branch if they want to track multiple separate agents,
        but rather create a branch for every new agent.
        """

        root = root if root else MetaNode(
            player=None, parent=None, branch=root_branch
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

        Args: TODO:
            parameters (Any): The parameters of the model to commit.
                Defaults to None
            hyperparameters (Dict[str, Any]): The hyperparameters to commit.
                Defaults to an empty dict.
            interaction (Interaction): The agents other than the parent that
                contributed to the last training step (opponents, allies,
                mates...). Defaults to an empty list.
            name (str): A unique identifier for the commit (like the commit
                hash in git). If this is None, an unique name will be
                generated using cryptographic hashing. Defaults to None
            pre_commit_hooks (List[PreCommitHooks]):
            post_commit_hooks (List[PostCommitHooks]):

        Raises:
            ValueError: If a player with the specified name already exists

        Returns:
            str: The id_str of the new commit.
        """
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

        Args:
            name (str): The name of the new branch. Must be unique.
                This will be a new alias to the current commit. If None, it
                returns the name of the active branch

        Raises:
            ValueError: If a player with the specified name/alias already
            exists

        Returns:
            str: The name of the new commit"""

        if name is None:
            return self._branch

        if self.repo.exists(name):
            raise ValueError(POPUPLATION_BRANCH_EXISTS.format(name))

        self.repo.branch(name, self._player)

        return self.checkout(name)

    def checkout(self, name: str) -> str:
        """Set the current branch to the one specified.

        Args:
            name (str): The name of the branch or player to switch to.

        Raises:
            ValueError: If there is no branch with the specified name"""

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
        """Returns a set of all branches"""
        return set(self.repo._branches)

    def head(self) -> 'Player':
        return self._player

    def detach(
        self,
    ) -> 'Population':
        """Creates a Population with the current player as root.

        The new Population does not have any connection to the current one,
        hence this should be thread-safe. This may then be reattached once
        operations have been performed.

        Returns:
            Population: A new population with the current player as
            root.
        """
        # TODO: detach persistence
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

        Args:
            population (Population): The population to merge in the current
                object. It's root's id_str should correspond to the id_str of
                an already existing node, which is where it will be attached.
            id_hook (Callable[[str], str]): A function that takes the current
                id_str of every commit in population and returns a new id_str
                to be used when attaching. Note that if auto_rehash is set to
                true, it happens before id_hook is called, hence the new
                hashes is what this function will receive as argument.
                Defaults to the identity function.
            auto_rehash (bool): If set to true, re-generates an id_str for
                every commit before attaching.

        Raises:
            ValueError: If the population's root's id_str does not match any
                current commit.
            ValueError: If there is a collision between commit id_str.
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
