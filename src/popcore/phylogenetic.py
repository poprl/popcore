from typing import List, Dict, Any
import string
import random
import warnings


class Player:
    def __init__(self,
                 parent: 'Player | None' = None,
                 model_parameters: Any = None,
                 id_str: str = '',
                 hyperparameters: Dict[str, Any] = {},
                 contributors: 'List[Player]' = [],
                 generation: int = 0,
                 timestep: int = 1,
                 force_save: bool = False):

        """A specific version of an agent at a given point in time.

        This is equivalent to a commit in the population.

        Args:
            parent (Player | None): The parent of this node.
                If None, this is considered a root. Every node may only
                have one parent, but if it needs more, it can have
                arbitrarily many contributors. Defaults to None
            model_parameters (Any): The parameters of the model. With
                neural networks, that would be the weights and biases.
                Defaults to None.
            id_str (str): The id_str of the node to find it in the population.
                id_strs must be unique within each pop. Defaults to the empty
                string.
            hyperparameters (Dict[str, Any]): A dictionary of the
                hyperparameters that define the transition from the parent
                to this node. This should contain enough information to
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
            generation (int): The generation this node belongs to.
                Defaults to 1.
            timestep (int): The timestep when this node was created.
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
        self.timestep: int = timestep   # TODO: Remove

        # Parameters to reproduce evolution from parent
        self.hyperparameters: Dict[str, Any] = hyperparameters

    def add_child(self, model_parameters=None,
                  id_str: str = '',
                  hyperparameters: Dict[str, Any] = {},
                  contributors: 'List[Player]' = [],
                  new_generation: bool = True) -> 'Player':

        """Adds a child to this node

        If `node` is directly specified then it will be added as a child.
        Otherwise, the other parameters will be used to create a new node
        and add it as a child.

        If force_save is true, the model will be kept. Otherwise it will
        be discarded if deemed unnecessary given the tree sparsity
        settings.

        Args:
            model_parameters (Any): The model parameters of the child to be
                added. If force_save is true, they will be kept no matter
                what. Otherwise they will be discarded if deemed
                unnecessary given the tree sparsity settings.
                Defaults to None.
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
            force_save (bool): If set to False, the model parameters will
                be discarded if judged unnecessary based on the tree
                sparsity parameter to save space. If set to true, the
                model parameters will be kept no matter what.

        Returns:
            PhylogeneticTree.Node: The new child

        Raises:
            ValueError: If the id_str conflicts with an other node in the tree.
        """

        # Create child node
        child = Player(
            self,
            id_str=id_str,
            model_parameters=model_parameters,
            hyperparameters=hyperparameters,
            contributors=contributors,
            generation=self.generation+1)

        if new_generation:
            child.generation = self.generation + 1
        else:
            child.generation = self.generation

        self.children.append(child)

        return child

    def get_nbr_unsaved_ancestors(self) -> int:
        """Returns the number of ancestors that would need to be
        recomputed in order to get the parameters of this model.

        Note that contributors count as ancestors"""

        if self.model_parameters is not None:
            return 0

        if self.parent is None:
            return 99999999999999999999999

        ancestors = [self.parent] + self.contributors

        return 1 + sum([x.get_nbr_unsaved_ancestors() for x in ancestors])

    def rebuild_model_parameters(self, save: bool = False,
                                 recursive: bool = False) -> Any:

        """Deprecated, do not use, kept for later re-implementation.

        Returns the parameters of the model corresponding with this
        node.

        If self.model_parameters is not None, the parameters will be
        returned directly. Otherwise, they will have to be recomputed
        with the step function using the hyperparameters, parent and
        contributors. Since the parents and contributors might also not
        have their model parameters saved, this is a recursive function,
        and the maximum number of calls is limited by the tree_sparseness
        parameter defined when initializing the phylogenetic tree.

        Args:
            save (bool): If set to true, the parameters of this model will
                be saved so that they don't have to be recomputed every
                time. Defaults to False.
            recursive (bool): If save and recursive are set to true, the
                parameters of all the ancestors computed will also be
                saved. If save is False, this does nothing.
                Defaults to False.

        Returns:
            Any: The parameters of the model that corresponf to this node.
        """

        warnings.warn("rebuild_model_parameters is deprecated, and is only "
                      "kept for later re-implementation. "
                      "It should not be used",
                      DeprecationWarning)

        if self.model_parameters is not None:
            return self.model_parameters

        contributors_param = [x.rebuild_model_parameters()
                              for x in self.contributors]

        if self.parent is not None:
            parent_param = self.parent.rebuild_model_parameters(
                save if recursive else False, recursive)

        model_parameters, _ = self.tree.step_function(
            parent_param,
            self.hyperparameters,
            contributors_param)

        if save:
            self.model_parameters = model_parameters

        return model_parameters


class Population:
    """A data structure to manipulate evolving populations of agents.
    The structure is meant to be similar to that of a git repository, where
    every branch corresponds to an agent."""

    def __init__(self,
                 sparsity: int = 100):
        """Instantiates population of agents.

        This is a data structure that records the evolution of populations of
        agents. It behaves like a git repository, where each branch is a
        unique agent and every commit corresponds to a specific iteration of
        said agent.

        This is initialized with a '_root' branch. Users should not commit
        directly to this branch if they want to track multiple separate agents,
        but rather create a branch for every new agent.

        Args:
            sparsity (int): How many unsaved ancestors any given agent can
                have.  Higher sparsity means the population will be lighter in
                memory, but getting non-saved agents will take longer (as all
                the ancestors need to be re-computed).
                Defaults to 100.
        """

        self._root = Player(id_str="_root")
        self.sparsity = sparsity

        # A dictionary containing all nodes in the tree
        self.nodes: Dict[str, Player] = {"_root": self._root}

        # An array of every node indexed by generation (1st gen has index 0)
        self.generations: List[List[Player]] = [[]]

        # A list of all branches 
        self.branches: Dict[str, Player] = {"_root": self._root}

        self.current_node = self._root
        self.current_branch = "_root"

    def __generate_id(self, id_str: str = ''):
        """Generate random unique id_str for a new node/commit

        Args:
            id_str (str): The id_str we want the new node to have. If this is
                the empty string, a random one will be generated. Defaults to
                the empty string.

        Raises:
            ValueError: If a node with the specified id_str already exists"""

        if id_str in self.nodes.keys():
            raise ValueError(f"A commit with id_str {id_str} already exists. "
                             "Every commit must have unique id_str")

        if id_str == '':
            while id_str == '' or id_str in self.nodes.keys():
                id_str = ''.join(
                    random.choice(string.ascii_letters + string.digits)
                    for i in range(32))

        return id_str

    def commit(self, model_parameters: Any = None,
               hyperparameters: Dict[str, Any] = {},
               contributors: 'List[Player]' = [],
               id_str: str = '') -> str:
        """Creates a new commit in the current branch.

        Args:
            model_parameters (Any): The parameters of the model to commit.
                Defaults to None
            hyperparameters (Dict[str, Any]): The hyperparameters to commit.
                Defaults to an empty dict.
            contributors (List[Player]): The agents other than the parent that
                contributed to the last training step (opponents, allies,
                mates...). Defaults to an empty list.
            id_str: A unique identifier for the commit (like the commit hash
                in git). If this is the empty string, an id_str will be
                generated at random. This value must be unique in the
                Population to uniquely identify each commit. Defaults to the
                empty string

        Raises:
            ValueError: If a commit with the specified id_str already exists

        Returns:
            str: The id_str of the new commit.
        """

        id_str = self.__generate_id(id_str)

        # Create the child node
        child = self.current_node.add_child(
            id_str=id_str,
            hyperparameters=hyperparameters,
            contributors=contributors)

        if child.get_nbr_unsaved_ancestors() > self.sparsity:
            child.model_parameters = model_parameters

        # Update the dict of nodes
        self.nodes[id_str] = child

        if len(self.generations) <= child.generation:
            self.generations.append([])
        self.generations[child.generation].append(child)

        self.current_node = child
        self.branches[self.current_branch] = self.current_node

        return id_str

    def branch(self, branch_name: str, id_str: str = '') -> str:
        """Create a new branch diverging from the current branch.

        Args:
            branch_name (str): The name of the new branch. Must be unique.
            id_str (str): The id_str of the commit that will be created by
                making a new branch. If this is the empty string, a new one
                will be generated at random. Must be unique. Defaults to the
                emtpy string

        Raises:
            ValueError: If a commit with the specified id_str already exists

        Returns:
            str: The id_str of the new commit"""

        id_str = self.__generate_id(id_str)
        new_node = self.current_node.add_child(
            model_parameters=self.current_node.model_parameters,
            hyperparameters=self.current_node.hyperparameters,
            new_generation=False,
            id_str=id_str)

        if branch_name in self.branches.keys():
            raise ValueError(f"A branch with the name '{branch_name}' already"
                             " exists")

        self.branches[branch_name] = new_node
        self.nodes[new_node.id_str] = new_node

        return id_str

    def checkout(self, branch_name: str) -> None:
        """Set the current branch to the one specified.

        Args:
            branch_name (str): The name of the branch to switch to.

        Raises:
            KeyError: If there is no branch with the specified name"""

        if branch_name not in self.branches.keys():
            raise KeyError(f"A branch with name '{branch_name}' does not"
                           " exist")

        self.current_branch = branch_name
        self.current_node = self.branches[branch_name]

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

    def get_branches(self) -> List[str]:
        """Return a list of all branches"""
        return list(self.branches.keys())

    def get_current_branch(self) -> str:
        """Return the name of the current branch"""
        return self.current_branch
