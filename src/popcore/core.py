from typing import (
    Generic, List, Dict, Any, Callable, Set, Iterator, TypeVar
)
from itertools import chain

from .hooks import AutoIdHook, PreCommitHook, PostCommitHook
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
        name: str = None,
        parent: 'Player' = None,
        parameters: Dict[str, Any] = None,
        hyperparameters: Dict[str, Any] = None,
        interaction: 'Interaction' = None,
        generation: int = 0,
        timestep: int = 1,
        branch: str = None
    ):

        """A specific version of an agent at a given point in time.

        This is equivalent to a commit in the population.

        Args:
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
        self.descendants: List[Player] = []

        self.parameters = parameters
        self.hyperparameters: Dict[str, Any] | None = hyperparameters

        self.interaction = interaction

        self.generation: int = generation
        self.timestep: int = timestep

        # Parameters to reproduce evolution from parent

        self.branch = branch

    def add_descendant(
        self,
        name: str = None,
        parameters: Any = None,
        hyperparameters: Dict[str, Any] = None,
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
            self,
            name=name,
            parameters=parameters,
            hyperparameters=hyperparameters,
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
        timestep: int = 0
    ):
        """_summary_

        Args:
            players (List[Player]): _description_
            outcomes (List[OUTCOME]): _description_
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

    def __init__(self, root_name: str = "_root"):
        """Instantiates population of agents.

        This is a data structure that records the evolution of populations of
        agents. It behaves like a git repository, where each branch is a
        unique agent and every commit corresponds to a specific iteration of
        said agent.

        This is initialized with a '_root' branch. Users should not commit
        directly to this branch if they want to track multiple separate agents,
        but rather create a branch for every new agent.
        """

        self._root = Player(name=root_name, branch=root_name)

        # A dictionary containing all commits in the tree
        # Multiple keys may refer to the same commit. In particular, branches
        # are aliases to specific commits
        self.nodes: Dict[str, Player] = {root_name: self._root}

        # An array of every node indexed by generation (1st gen has index 0)
        self.generations: List[List[Player]] = [[]]

        self.player: Player = self._root
        self._branch: str = root_name

        self._branches: Set[str] = set([root_name])
        self._default_pre_commit_hooks = [
            AutoIdHook()
        ]
        self._default_post_commit_hooks = [

        ]

    def _add_gen(self, player: Player):
        if len(self.generations) <= player.generation:
            self.generations.append([])
        self.generations[player.generation].append(player)

    def commit(
        self,
        parameters: Any = None,
        hyperparameters: Dict[str, Any] | None = None,
        interaction: "Interaction | None" = None,
        name: str = None,
        timestep: int = 1,
        pre_commit_hooks: List[PreCommitHook] = None,
        post_commit_hooks: List[PostCommitHook] = None
    ) -> str:
        """Creates a new commit in the current branch.

        Args:
            model_parameters (Any): The parameters of the model to commit.
                Defaults to None
            hyperparameters (Dict[str, Any]): The hyperparameters to commit.
                Defaults to an empty dict.
            contributors (List[Player]): The agents other than the parent that
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
        next_player = self.player.add_descendant(
            name=name,
            parameters=parameters,
            hyperparameters=hyperparameters,
            interaction=interaction,
            timestep=timestep,
            branch=self._branch
        )

        # TODO: Pre Commit Hook Logic
        for hook in chain(
            self._default_pre_commit_hooks, pre_commit_hooks
        ):
            hook(self, next_player)

        if next_player.name in self.nodes.keys():
            raise ValueError(POPULATION_COMMIT_EXIST.format(name))
        self.nodes[next_player.name] = next_player

        self._add_gen(next_player)

        self.player = next_player
        self.nodes[self._branch] = self.player

        # TODO: Post Commit Hook Logic
        for hook in post_commit_hooks:
            hook(self, next_player)

        return next_player.name

    def branch(self, name: str, auto_name: bool = False) -> str:
        """Create a new branch diverging from the current branch.

        Args:
            name (str): The name of the new branch. Must be unique.
                This will be a new alias to the current commit
    
        Raises:
            ValueError: If a commit with the specified id_str already exists

        Returns:
            str: The id_str of the new commit"""

        if name in self.nodes.keys():
            raise ValueError(POPUPLATION_BRANCH_EXISTS.format(name))

        self.nodes[name] = self.player
        self._branches.add(name)

        return name

    def checkout(self, name: str) -> None:
        """Set the current branch to the one specified.

        Args:
            name (str): The name of the branch or player to switch to.

        Raises:
            ValueError: If there is no branch with the specified name"""

        if name not in self.nodes.keys():
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))

        self.player = self.nodes[name]

        if name in self._branches:
            self._branch = name
        else:
            self._branch = self.player.branch

    def __get_commit(self, name: str = None) -> Player:
        """Returns the commit with the given id_str if it exists.

        Args:
            name (str): The name of the commit we are trying to get. If
                id_str is the empty string, returns the latest commit of the
                current branch. Defaults to the empty string.

        Raises:
            ValueError: If a commit with the specified `name` does not exist"""

        if name is None:
            return self.player

        if name not in self.nodes.keys():
            raise ValueError(POPULATION_PLAYER_NOT_EXIST.format(name))

        return self.nodes[name]

    def __get_commits(self, id_strs: List[str]) -> List[Player]:
        """Returns the commit with the given id_str if it exists.

        Args:
            id_strs (List[str]): The id_str of the commits we are trying to
                get.

        Raises:
            KeyError: If a commit with one of the specified id_str does not
                exist
        """

        return [self.__get_commit(c) for c in id_strs]

    def __get_commit_history(self, id_str: str = "") -> List[str]:
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

        commit: None | Player  # Mypy cries if I don't specify that

        if id_str == "":
            commit = self.player
        else:
            if id_str not in self.nodes.keys():
                raise KeyError(f"The commit {id_str} does not exist")
            commit = self.nodes[id_str]

        history = [commit.name]
        commit = commit.parent
        while commit is not None:
            history.append(commit.name)
            commit = commit.parent

        return history

    def __get_descendents(self, id_str: str = "") -> List[str]:
        """Returns a list of all id_str of commits that came after the one
        with specified id_str, including branches.

        If id_str is not specified, it will default to the current commit.
        The list is of all commits that originate from the specified commit.

        The list returned is in no particular order."""

        commit: None | Player  # Mypy cries if I don't specify that

        if id_str == "":
            commit = self.player
        else:
            if id_str not in self.nodes.keys():
                raise KeyError(f"The commit {id_str} does not exist")
            commit = self.nodes[id_str]

        history = [commit.name]
        for c in commit.descendants:
            history.extend(self.__get_descendents(c.name))

        return history

    def walk_lineage(self, branch: str = "") -> Iterator[Player]:
        """Returns an iterator with the commits in the given lineage"""
        lineage = self.__get_commit_history(branch)[:-1]
        for i in self.__get_commits(lineage):
            yield i

    def walk_gen(self, gen: int = -1) -> Iterator[Player]:
        """Returns an iterator with the commits in the given generation"""
        for i in self.generations[gen]:
            yield i

    def walk(self) -> Iterator[Player]:
        """Returns an iterator with all the commits in the population"""
        lineage = self.__get_descendents(self._root.name)[1:]
        for i in self.__get_commits(lineage):
            yield i

    def branches(self) -> Set[str]:
        """Return a set of all branches"""
        return self._branches

    def get_current_branch(self) -> str:
        """Return the name of the current branch"""
        return self._branch

    def detach(self) -> 'Population':
        """Creates a Population with the current commit's id_str as root_id.

        The new Population does not have any connection to the current one,
        hence this should be thread-safe. This may then be reattached once
        operations have been performed.

        Returns:
            Population: A new population with the current commit's id_str as
            root_id.
        """

        detached_pop = Population(root_name=self.player.name)
        return detached_pop

    def attach(self, population: 'Population',
               id_hook: Callable[[str], str] = lambda x: x,
               auto_rehash: bool = False) -> None:
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

        # Warning: If a model is saved in a detached pop, and the pop is then
        # reattached, the re-hashing of the commits might make the model not
        # loadable anymore since the id_str changed (so in case either id_hook
        # is provided ot auto_rehash is true)

        if population._root.name not in self.nodes.keys():
            raise ValueError("The population's root's id_str does not match "
                             "any known commit, hence it cannot be attached")

        node = self.nodes[population._root.name]

        for x in population._root.descendants:
            node.descendants.append(x)
            x.parent = node

        nodes_to_add = {}
        branches_to_add = set()
        branch_renaming = {}

        for branch in population._branches:
            new_branch = branch
            i = 1
            while new_branch in self.nodes.keys():
                new_branch = branch + str(i)
                i += 1

            branches_to_add.add(new_branch)
            branch_renaming[branch] = new_branch

        for id_str, player in population.nodes.items():

            if id_str == population._root.name:
                continue

            if id_str in population._branches:
                nodes_to_add[branch_renaming[id_str]] = player
                continue

            new_id_str = id_str

            if auto_rehash:
                new_id_str = self._generate_id('', player)

            new_id_str = id_hook(new_id_str)
            player.name = new_id_str
            player.branch = branch_renaming[player.branch]

            if id_str in self.nodes.keys():
                raise ValueError("Collision between id_str of commits from "
                                 "both populations.")

            self.nodes[player.name] = player

            self._add_gen(player)

        self.nodes.update(nodes_to_add)
        self._branches = self._branches.union(branches_to_add)
