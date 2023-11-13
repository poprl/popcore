import os
from typing import (
    Generic, List, Dict, Set, TypeVar, Optional
)
from itertools import chain

from .hooks import (
    AutoIdHook, PreCommitHook, PostCommitHook, AttachHook,
    ReIdHook
)
from .errors import (
    POPULATION_COMMIT_EXIST, POPUPLATION_BRANCH_EXISTS,
    POPULATION_PLAYER_NOT_EXIST
)

OUTCOME = TypeVar("OUTCOME")


class Player:
    """
        Player
    """
    def __init__(
        self,
        name: Optional[str] = None,
        parent: 'Optional[Player]' = None,
        interaction: 'Optional[Interaction]' = None,
        generation: Optional[int] = 0,
        timestep: Optional[int] = 1,
        branch: Optional[str] = None,
        persistence: Optional[str] = None
    ):

        """A specific version of an agent at a given point in time.

        This is equivalent to a commit in the population.

        Args: TODO
            parent (Player | None): The parent of this player.
                If None, this is considered a root. Every player may only
                have one parent, but if it needs more, it can have
                arbitrarily many contributors. Defaults to None
            model_parameters (Any): The parameters of the model. With
                neural networks, that would be the weights and biases.
                Defaults to None.
            id_str (str): The id_str of the player to find it in the pop.
                id_strs must be unique within each pop. Defaults to the empty
                string.
            hyperparameters (Dict[str, Any]): A dictionary of the
                hyperparameters that define the transition from the parent
                to this player. This should contain enough information to
                reproduce the evolution step deterministically given the
                parent and contributors parameters.
                Defaults to an empty dict.
            contributors (List[PhylogeneticTree.Node]): All the models
                other than the parent that contributed to the evolution.
                Typically, that would be opponents and allies, or mates in
                the case of genetic crossover.
                For example, if the model played a game of chess against
                an opponent and learned from it, the parent would be the
                model before that game, and the contributor would be the
                opponent. Defaults to an empty list.
            generation (int): The generation this player belongs to.
                Defaults to 1.
            timestep (int): The timestep when this player was created.
                Defaults to 1.

        Raises:
            KeyError: If hyperparameters does not contain one of the
                variables that were defined as necessary when creating the
                tree.
            ValueError: If the id_str conflicts with an other node in the tree.
        """
        self.name = name
        self.parent = parent
        self.path: str = ''
        self.descendants: List[Player] = []

        self.interaction = interaction

        self.generation: int = generation
        self.timestep: int = timestep

        self.branch = branch
        self.persistence = persistence

    def add_descendant(
        self,
        name: str = None,
        interaction: 'Interaction' = None,
        timestep: int = 1,
        branch: str = None
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
        descendant = Player(
            name=name,
            parent=self,
            interaction=interaction,
            generation=self.generation + 1,
            timestep=timestep,
            branch=branch
        )

        self.descendants.append(descendant)

        return descendant

    def has_descendants(self) -> bool:
        return len(self.descendants) > 0


class Team(Player):
    """
       Team
    """
    members: "list[Player]"

    def __init__(self, name: str, members: "list[Player]"):
        self.members = members
        super().__init__(name)


class Interaction(Generic[OUTCOME]):
    """_summary_
        players: players involved in the game
        scores: outcomes for each player involved in the game
    """

    def __init__(
        self,
        players: List[Player],
        outcomes: List[OUTCOME],
        timestep: int
    ):
        """_summary_

        Args:
            players (List[Player]): TODO _description_
            outcomes (List[OUTCOME]): TODO _description_
            timestep (int): TODO: description
        """
        assert len(players) == len(outcomes)
        assert timestep >= 0
        self._players = players
        self._outcomes = outcomes
        self._timestep = timestep

    @property
    def players(self):
        return self._players

    @property
    def outcomes(self):
        return self._outcomes

    @property
    def timestep(self):
        return self._timestep


class Population:
    """A data structure to manipulate evolving populations of agents.
    The structure is meant to be similar to that of a git repository, where
    every branch corresponds to an agent."""

    def __init__(
        self,
        stage: str = None,
        root: 'Optional[Player]' = None,
        root_name: str = "_root",
        root_branch: str = "main",
        pre_commit_hooks: Optional[List[PreCommitHook]] = None,
        post_commit_hooks: Optional[List[PostCommitHook]] = None,
        attach_hooks: Optional[List[AttachHook]] = None,
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

        root = root if root else Player(
            parent=None, name=root_name, branch=root_branch
        )
        self._root = root

        # Need to separate root.name and rootbranch otherwise if a commit is
        # made to _root, it updates the _root branch to point at the new commit
        # and we lose the access to the root commit.
        self._stage = os.path.join(stage, '.pop') if stage else '.pop'
        os.makedirs(self._stage, exist_ok=True)

        # A dictionary containing all commits in the tree
        # Multiple keys may refer to the same commit. In particular, branches
        # are aliases to specific commits
        self._nodes: Dict[str, Player] = {
            root_name: self._root,
            root_branch: self._root
        }

        # An array of every node indexed by generation (1st gen has index 0)
        self._generations: List[List[Player]] = [[]]

        self._player: Player = self._root
        self._branch: str = self._root.branch

        self._branches: Set[str] = set([self._branch])

        # Pre-Commit Hooks
        self._pre_commit_hooks: List[PreCommitHook] = [
            AutoIdHook()
        ]
        self._pre_commit_hooks += pre_commit_hooks if pre_commit_hooks else []
        # Post-Commit Hooks
        self._post_commit_hooks: List[PostCommitHook] = []
        self._post_commit_hooks += post_commit_hooks if post_commit_hooks else []
        # Attach Hooks
        self._attach_hooks: List[AttachHook] = [
            ReIdHook()
        ]
        self._attach_hooks += attach_hooks if attach_hooks else []

    def commit(
        self,
        name: str = None,
        interaction: "Interaction | None" = None,
        timestep: int = 1,
        pre_commit_hooks: List[PreCommitHook] | None = None,
        post_commit_hooks: List[PostCommitHook] | None = None,
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

        # Create the child node
        next_player = self._player.add_descendant(
            name=name,
            interaction=interaction,
            timestep=timestep,
            branch=self._branch
        )

        pre_commit_hooks = pre_commit_hooks if pre_commit_hooks else []
        for hook in chain(
            self._pre_commit_hooks, pre_commit_hooks
        ):
            hook(self, next_player, **kwargs)

        if next_player.name in self._nodes:
            raise ValueError(POPULATION_COMMIT_EXIST.format(name))

        self._nodes[next_player.name] = next_player

        self._add_gen(next_player)

        self._player = next_player
        self._nodes[self._branch] = self._player

        post_commit_hooks = post_commit_hooks if post_commit_hooks else []
        for hook in chain(
            self._post_commit_hooks, post_commit_hooks
        ):
            hook(self, next_player, **kwargs)

        return next_player.name

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

        if name in self._nodes:
            raise ValueError(POPUPLATION_BRANCH_EXISTS.format(name))

        self._nodes[name] = self._player
        self._branches.add(name)

        return name

    def checkout(self, name: str) -> str:
        """Set the current branch to the one specified.

        Args:
            name (str): The name of the branch or player to switch to.

        Raises:
            ValueError: If there is no branch with the specified name"""

        if name not in self._nodes:
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))

        self._player = self._nodes[name]

        if name in self._branches:
            self._branch = name
        else:
            self._branch = self._player.branch

        return self._branch

    def branches(self) -> Set[str]:
        """Returns a set of all branches"""
        return self._branches

    def detach(
        self,
        stage: str
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
            stage=stage,
            root=self._player,
            pre_commit_hooks=self._pre_commit_hooks,
            post_commit_hooks=self._post_commit_hooks,
            attach_hooks=self._attach_hooks,
        )
        return detached_pop

    def attach(
        self,
        population: 'Population',
        attach_hooks: Optional[List[AttachHook]] = None
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
        if population._root.name not in self._nodes:
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(
                population._root.name))

        # Pick the right place to reattach
        node = self._nodes[population._root.name]

        # Transfer all the nodes from the other pop to the right place
        for player in population._root.descendants:
            node.descendants.append(player)
            player.parent = node

        nodes_to_add = {}

        # Rename branches in attached pop to avoid conflicts
        branches_to_add, branch_renaming = self._rename_conflicting_branches(
            population
        )

        attach_hooks = attach_hooks if attach_hooks else []
        for name, player in population._nodes.items():
            # Ignore root node
            if name == population._root.name:
                continue

            # Add the renamed branches to the main pop
            if name in population._branches:
                nodes_to_add[branch_renaming[name]] = player
                continue

            # Apply branch renaming
            player.branch = branch_renaming[player.branch]

            player.generation += node.generation

            # Apply hooks
            for hook in chain(
                self._attach_hooks, attach_hooks
            ):
                hook(self, player)

            if name in self._nodes:
                raise ValueError(POPULATION_COMMIT_EXIST.format(name))

            # Add player to the index
            self._nodes[player.name] = player

            self._add_gen(player)

        # Add branches to the index
        self._nodes.update(nodes_to_add)
        self._branches = self._branches.union(branches_to_add)

    def head(self) -> 'Player':
        return self._player

    def stage(self) -> str:
        return self._stage

    def _rename_conflicting_branches(self, population: 'Population'):
        """Every branch that generates a conflict gets renamed by adding an
        integer at the end"""

        branches_to_add = set()
        branch_renaming = {}

        for branch in population._branches:
            new_branch = branch
            i = 1
            while new_branch in self._nodes:
                new_branch = branch + str(i)
                i += 1

            branches_to_add.add(new_branch)
            branch_renaming[branch] = new_branch

        return branches_to_add, branch_renaming

    def _add_gen(self, player: Player):
        if len(self._generations) <= player.generation:
            self._generations.append([])
        self._generations[player.generation].append(player)
