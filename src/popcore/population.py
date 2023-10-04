from typing import List, Dict, Any, Callable, Set
from hashlib import sha1

# TODO: Saving/loading whole population (not in MVP, do later)
# TODO: pop.fork() -> Population (not in MVP, for later)
# TODO: pop.merge(Population) -> Population (not in MVP, for later)


class Player:
    def __init__(self,
                 parent: 'Player | None' = None,
                 model_parameters: Any = None,
                 id_str: str = '',
                 hyperparameters: Dict[str, Any] | None = None,
                 contributors: 'List[Player] | None' = None,
                 generation: int = 0,
                 timestep: int = 1,
                 branch_name: str = ''):

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

        self.parent = parent
        self.children: List[Player] = []
        self.model_parameters = model_parameters

        # All the other models this transition depended on
        # (opponents/allies for RL, other parent in genetics...)
        self.contributors = contributors
        #

        self.id_str = id_str
        self.generation: int = generation
        self.timestep: int = timestep

        # Parameters to reproduce evolution from parent
        self.hyperparameters: Dict[str, Any] | None = hyperparameters

        self.branch_name = branch_name

    def add_child(self, model_parameters=None,
                  id_str: str = '',
                  hyperparameters: Dict[str, Any] | None = None,
                  contributors: 'List[Player] | None' = None,
                  new_generation: bool = True,
                  timestep: int = 1,
                  branch_name: str = '') -> 'Player':

        """Adds a child to this node

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
            contributors (List[PhylogeneticTree.Node]): All the models
                other than the parent that contributed to the evolution.
                Typically, that would be opponents and allies, or mates in
                the case of genetic crossover.
                For example, if the model played a game of chess against
                an opponent and learned from it, the parent would be the
                model before that game, and the contributor would be the
                opponent. Defaults to an empty list.

        Returns:
            PhylogeneticTree.Node: The new child

        Raises:
            ValueError: If the id_str conflicts with an other node in the tree.
        """

        branch_name = self.branch_name if branch_name == '' else branch_name

        # Create child node
        child = Player(
            self,
            id_str=id_str,
            model_parameters=model_parameters,
            hyperparameters=hyperparameters,
            contributors=contributors,
            generation=self.generation+1,
            timestep=timestep,
            branch_name=branch_name)

        if new_generation:
            child.generation = self.generation + 1
        else:
            child.generation = self.generation

        self.children.append(child)

        return child

    def has_child(self) -> bool:
        return len(self.children) > 0

    def load_model_parameters(self, load_hook: Callable[[str], Any]):
        return load_hook(self.id_str)


class Population:
    """A data structure to manipulate evolving populations of agents.
    The structure is meant to be similar to that of a git repository, where
    every branch corresponds to an agent."""

    def __init__(self, root_id="_root"):
        """Instantiates population of agents.

        This is a data structure that records the evolution of populations of
        agents. It behaves like a git repository, where each branch is a
        unique agent and every commit corresponds to a specific iteration of
        said agent.

        This is initialized with a '_root' branch. Users should not commit
        directly to this branch if they want to track multiple separate agents,
        but rather create a branch for every new agent.
        """

        self._root = Player(id_str=root_id, branch_name=root_id)

        # A dictionary containing all commits in the tree
        # Multiple keys may refer to the same commit. In particular, branches
        # are aliases to specific commits
        self.nodes: Dict[str, Player] = {root_id: self._root}

        # An array of every node indexed by generation (1st gen has index 0)
        self.generations: List[List[Player]] = [[]]

        self.current_node: Player = self._root
        self.current_branch: str = root_id

        self.branches: Set[str] = set([root_id])

    def __generate_id(self, id_str: str = '', node: Player | None = None
                      ) -> str:
        """Generate random unique id_str for a new node/commit

        Args:
            id_str (str): The id_str we want the new node to have. If this is
                the empty string, one will be generated using sha1. Defaults to
                the empty string.

        Raises:
            ValueError: If a commit with the specified id_str already exists"""

        if id_str != '':
            return id_str

        if node is None:
            node = self.current_node
        path = ''
        while node is not None:
            path += str(node)
            node = node.parent
        id_str = sha1(path.encode()).hexdigest()

        return id_str

    def __add_gen(self, player):
        if len(self.generations) <= player.generation:
            self.generations.append([])
        self.generations[player.generation].append(player)

    def commit(self, model_parameters: Any = None,
               hyperparameters: Dict[str, Any] | None = None,
               contributors: 'List[Player] | None' = None,
               id_str: str = '',
               timestep: int = 1,
               id_hook: Callable[[str], str] = lambda x: x,
               player_hook: Callable[[Player], Player] = lambda x: x,
               persist_hook: Callable[[str, Player], None] = lambda x, y: None
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
            id_str (str): A unique identifier for the commit (like the commit
                hash in git). If this is the empty string, an id_str will be
                generated using sha1. This value must be unique in the
                Population to uniquely identify each commit. Defaults to the
                empty string
            id_hook (Callable[[str], str]): A function that takes id_str if
                provided, or the automatically generated hash if not, and
                returns a new id_str. This will be the hash of the commit,
                hence the result must be unique. This is meant to allow user
                to customize population indexing. Defaults to the identity
                function.
            player_hook (Callable[[Player], Player]): A function that takes
                the newly created Player object and returns a new one to be
                added to the population instead. This is meant to allow users
                to customize player creation. Defaults to the identity
                function.
            persist_hook (Callable[[str, Player], Player]): A function that
                takes the commit id_str and newly created Player object to
                save the corresponding model. This is meant to allow users
                to save any model they may be using. If it is provided, it
                will be called, so only give this argument if you want that
                specific version of the model to persist. Defaults to the None
                function.

        Raises:
            ValueError: If a commit with the specified id_str already exists

        Returns:
            str: The id_str of the new commit.
        """

        # Create the child node
        child = self.current_node.add_child(
            id_str=id_str,
            model_parameters=model_parameters,
            hyperparameters=hyperparameters,
            contributors=contributors,
            timestep=timestep,
            branch_name=self.current_branch)

        id_str = self.__generate_id(id_str, child)
        id_str = id_hook(id_str)

        if id_str in self.nodes.keys():
            raise ValueError(f"A commit with id_str {id_str} already exists. "
                             "Every commit must have unique id_str")

        child.id_str = id_str

        child = player_hook(child)

        # Update the dict of nodes
        self.nodes[id_str] = child

        self.__add_gen(child)

        self.current_node = child
        self.nodes[self.current_branch] = self.current_node

        persist_hook(id_str, child)

        return id_str

    def branch(self, branch_name: str) -> str:
        """Create a new branch diverging from the current branch.

        Args:
            branch_name (str): The name of the new branch. Must be unique.
                This will be a new alias to the current commit

        Raises:
            ValueError: If a commit with the specified id_str already exists

        Returns:
            str: The id_str of the new commit"""

        if branch_name in self.nodes.keys():
            raise ValueError(f"A branch with the name '{branch_name}' already"
                             " exists")

        self.nodes[branch_name] = self.current_node
        self.branches.add(branch_name)

        return branch_name

    def checkout(self, branch_name: str) -> None:
        """Set the current branch to the one specified.

        Args:
            branch_name (str): The name of the branch to switch to.

        Raises:
            KeyError: If there is no branch with the specified name"""

        if branch_name not in self.nodes.keys():
            raise KeyError(f"A branch with name '{branch_name}' does not"
                           " exist")

        self.current_node = self.nodes[branch_name]

        if branch_name in self.branches:
            self.current_branch = branch_name
        else:
            self.current_branch = self.current_node.branch_name

    def get_model_parameters(self):
        """Return the model parameters in the last commit of the current
        branch"""
        return self.current_node.model_parameters

    def get_commit(self, id_str: str = ""):
        """Returns the commit with the given id_str if it exists.

        Args:
            id_str (str): The id_str of the commit we are trying to get. If
                id_str is the empty string, returns the latest commit of the
                current branch. Defaults to the empty string.

        Raises:
            KeyError: If a commit with the specified id_str does not exist"""

        if id_str == "":
            return self.current_node

        if id_str not in self.nodes.keys():
            raise KeyError(f"The commit {id_str} does not exist")

        return self.nodes[id_str]

    def get_commit_history(self, id_str: str = "") -> List[str]:
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
            commit = self.current_node
        else:
            if id_str not in self.nodes.keys():
                raise KeyError(f"The commit {id_str} does not exist")
            commit = self.nodes[id_str]

        history = [commit.id_str]
        commit = commit.parent
        while commit is not None:
            history.append(commit.id_str)
            commit = commit.parent

        return history

    def get_branches(self) -> Set[str]:
        """Return a set of all branches"""
        return self.branches

    def get_current_branch(self) -> str:
        """Return the name of the current branch"""
        return self.current_branch

    def detach(self) -> 'Population':
        """Creates a Population with the current commit's id_str as root_id.

        The new Population does not have any connection to the current one,
        hence this should be thread-safe. This may then be reattached once
        operations have been performed.

        Returns:
            Population: A new population with the current commit's id_str as
            root_id.
        """

        detached_pop = Population(root_id=self.current_node.id_str)
        return detached_pop

    def attach(self, population: 'Population',
               id_hook: Callable[[str], str] = lambda x: x,
               auto_rehash: bool = True) -> None:
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

        # TODO: If a model is saved in a detached pop, and the pop is then
        # reattached, the re-hashing of the commits might make the model not
        # loadable anymore since the id_str changed.

        if population._root.id_str not in self.nodes.keys():
            raise ValueError("The population's root's id_str does not match "
                             "any known commit, hence it cannot be attached")

        node = self.nodes[population._root.id_str]

        for x in population._root.children:
            node.children.append(x)
            x.parent = node

        nodes_to_add = {}
        branches_to_add = set()
        branch_renaming = {}

        for branch in population.branches:
            new_branch = branch
            i = 1
            while new_branch in self.nodes.keys():
                new_branch = branch + str(i)
                i += 1

            branches_to_add.add(new_branch)
            branch_renaming[branch] = new_branch

        for id_str, player in population.nodes.items():

            if id_str == population._root.id_str:
                continue

            if id_str in population.branches:
                nodes_to_add[branch_renaming[id_str]] = player
                continue

            new_id_str = id_str

            if auto_rehash:
                new_id_str = self.__generate_id('', player)

            new_id_str = id_hook(new_id_str)
            player.id_str = new_id_str
            player.branch_name = branch_renaming[player.branch_name]

            if id_str in self.nodes.keys():
                raise ValueError("Collision between id_str of commits from "
                                 "both populations.")

            self.nodes[player.id_str] = player

            self.__add_gen(player)

        self.nodes.update(nodes_to_add)
        self.branches = self.branches.union(branches_to_add)
