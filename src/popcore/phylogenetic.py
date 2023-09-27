from typing import List, Dict, Any, Callable
import string
import random
from copy import deepcopy

# Display libraries
import networkx as nx                                   # type: ignore
import matplotlib.pyplot as plt                         # type: ignore
from networkx.drawing.nx_pydot import graphviz_layout   # type: ignore


def undefined_step(model_parameters, hyperparameters, contributors):
    """The default step function"""
    raise ValueError("You did not provide a step function, hence the model "
                     "parameters that were not saved cannot be recovered")


class PhylogeneticTree:

    class Node:
        def __init__(self, tree: 'PhylogeneticTree',
                     parent: 'PhylogeneticTree.Node | None' = None,
                     model_parameters: Any = None,
                     ID: str = '',
                     hyperparameters: Dict[str, Any] = {},
                     contributors: 'List[PhylogeneticTree.Node]' = [],
                     generation: int = 1,
                     timestep: int = 1,
                     force_save: bool = False):

            """A node in the phylogenetic tree. This corresponds to a specific
            iteration of an individual.

            Args:
                tree (PhylogeneticTree): The tree this node belongs to
                parent (PhylogeneticTree.Node | None): The parent of this node.
                    If None, this is considered a root. Every node may only
                    have one parent, but if it needs more, it can have
                    arbitrarily many contributors. Defaults to None
                model_parameters (Any): The parameters of the model. With
                    neural networks, that would be the weights and biases.
                    Defaults to None.
                ID (str): The ID of the node to find it in the tree. IDs must
                    be unique within each tree. Defaults to the empty string.
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
                force_save (bool): If set to true, this ensures the model
                    parameters will not be discarded to save space. This
                    should be set to True for roots. Defaults to False.

            Raises:
                KeyError: If hyperparameters does not contain one of the
                    variables that were defined as necessary when creating the
                    tree.
                ValueError: If the ID conflicts with an other node in the tree.
            """

            self.tree = tree
            self.parent = parent
            self.children: List[PhylogeneticTree.Node] = []
            self.model_parameters = model_parameters
            self.force_save = force_save

            # All the other models this transition depended on
            # (opponents/allies for RL, other parent in genetics...)
            self.contributors = contributors
            #

            self.set_ID(ID)
            self.generation: int = generation
            self.timestep: int = timestep

            # Parameters to reproduce evolution from parent

            self.hyperparameters: Dict[str, Any] = hyperparameters

            # Check every hyperparameter is defined
            if parent is not None:
                for h in self.tree.hyperparameter_list:
                    if h not in self.hyperparameters.keys():
                        raise KeyError(f"The `{h}` hyperparameter was "
                                       "expected but not found")

            if len(tree.generations) < generation:
                tree.generations.append([])
            tree.generations[generation - 1].append(self)

        def set_ID(self, ID: str) -> None:

            """Sets the ID to the specified value.
            If the specified value is the empty string, one is generated
            randomly.

            Args:
                ID (str): The ID to create.

            Raises:
                ValueError: If the ID conflicts with an other node in the tree.
            """

            if ID in self.tree.nodes.keys():
                raise ValueError("A node with this ID already exists. "
                                 "Every node must have unique ID")

            # Generate random unique ID
            self.ID = ID
            if self.ID == '':
                while self.ID == '' or ID in self.tree.nodes.keys():
                    self.ID = ''.join(
                        random.choice(string.ascii_letters + string.digits)
                        for i in range(32))

        def set_tree(self, tree: 'PhylogeneticTree') -> None:

            """Changes the self.tree variable of this node and of it's
            offsprings to the new tree"""

            self.tree = tree
            if self.ID in self.tree.nodes.keys():
                self.set_ID('')
            self.tree.nodes[self.ID] = self
            for c in self.children:
                c.set_tree(tree)

        def add_child(self, model_parameters=None,
                      ID: str = '',
                      hyperparameters: Dict[str, Any] = {},
                      contributors: 'List[PhylogeneticTree.Node]' = [],
                      force_save: bool = False
                      ) -> 'PhylogeneticTree.Node':

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
                ID (str): The ID of the child. If this is the empty string, a
                    unique ID will be picked at random.
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
                ValueError: If the ID conflicts with an other node in the tree.
            """

            # Create child node
            child = PhylogeneticTree.Node(
                self.tree, self,
                ID=ID,
                hyperparameters=deepcopy(hyperparameters),
                contributors=contributors,
                generation=self.generation+1)

            child.generation = self.generation + 1
            if len(self.tree.generations) < child.generation:
                self.tree.generations.append([])
            self.tree.generations[child.generation - 1].append(child)

            if child.get_nbr_unsaved_ancestors() > self.tree.tree_sparsity:
                child.model_parameters = deepcopy(model_parameters)

            self.children.append(child)
            self.tree.nodes[child.ID] = child

            return child

        def get_model_parameters(self, save: bool = False,
                                 recursive: bool = False) -> Any:

            """Returns the parameters of the model corresponding with this
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

            if self.model_parameters is not None:
                return self.model_parameters

            contributors_param = [x.get_model_parameters()
                                  for x in self.contributors]

            if self.parent is not None:
                parent_param = self.parent.get_model_parameters(
                    save if recursive else False, recursive)

            model_parameters, _ = self.tree.step_function(
                parent_param,
                self.hyperparameters,
                contributors_param)

            if save:
                self.model_parameters = deepcopy(model_parameters)

            return model_parameters

        def get_nbr_unsaved_ancestors(self) -> int:
            """Returns the number of ancestors that would need to be
            recomputed in order to get the parameters of this model.

            Note that contributors count as ancestors"""

            if self.model_parameters is not None:
                return 0

            ancestors = [self.parent] + self.contributors if self.parent is\
                not None else self.contributors

            return 1 + sum([x.get_nbr_unsaved_ancestors() for x in ancestors])

    def __init__(self,
                 hyperparameter_names: list[str] = [],
                 step_function: Callable = undefined_step,
                 tree_sparsity: int = 100):
        """A phylogenetic tree.

        This is a data structure that records the evolution of populations of
        agents. Every node corresponds to a specific iteration of an agent, and
        every edge is an evolutionary/learning step.
        Saving the hyperparameters at every step should allow users to get the
        model parameters of any agent at any step without saving all of them,
        but rather by recomputing specific steps as needed.

        Note that since there may be multiple independent roots, this can
        technically handle phylogenetic forests.

        Args:
            hyperparameter_names (list[str]): The list of all the
                hyperparameters that define the transition from one iteration
                of an agent to the next. This should contain enough
                information to reproduce the evolution step deterministically
                given the parent and contributors parameters.
                For example, this could contain
                ["learning rate", "gamma", "ent-coef", "played as white", ...]
                Defaults to an empty list.
            step_function (Callable[[Any,
                                     Dict[str, Any],
                                     List[PhylogeneticTree.Node]],
                                    [Any, Dict[str, Any]]]):
                step_function(model_parameters, hyperparameters, contributors)
                is the step function during the training of models. It is a
                function that when given model parameters, a hyperparameters
                dictionary containing all necessary values and a list of
                contributor's parameters (opponents, allies, mates...)
                can deterministically return the parameters of the resulting
                model, and the updated hyperparameters.
                This means that if you give the initial model, the
                hyperparameters and the opponent(s) it faced to this function,
                it will return the updated model and the updated
                hyperparameters.
                If a stochastic process happens during transition from one
                model to the next, it must be seeded at each step for
                reproducability, and that seed saved as a hyperparameter.
                Defaults to undefined_step.
            tree_sparsity (int): How many unsaved ancestors any given node can
                have.  Higher sparsity means the tree will be lighter in
                memory, but getting non-saved nodes will take longer (as all
                the ancestors need to be re-computed).
                Defaults to 100."""

        # The list of 'roots', i.e. models without ancestors
        self.roots: List[PhylogeneticTree.Node] = []
        self.hyperparameter_list = hyperparameter_names
        self.step_function = step_function
        self.tree_sparsity = tree_sparsity

        # A dictionary containing all nodes in the tree
        self.nodes: Dict[str, PhylogeneticTree.Node] =\
            {root.ID: root for root in self.roots}

        # An array of every node indexed by generation (1st gen has index 0)
        self.generations: List[List[PhylogeneticTree.Node]] = []

    def add_root(self, model_parameters: Any, ID: str = ''
                 ) -> 'PhylogeneticTree.Node':

        """Add a root to the forest (A root is a node without ancestors).

        Args:
            model_parameters (Any): The parameters of the model corresponding
                to that node.
            ID (str): The ID of the new root. If set to the empty string, a
                random ID will be assigned. This must be unique.
                Defaults to the empty string.

        Returns:
            PhylogeneticTree.Node: The new node.
        """

        root = PhylogeneticTree.Node(
            tree=self,
            model_parameters=deepcopy(model_parameters),
            ID=ID,
            force_save=True)
        self.roots.append(root)
        self.nodes[root.ID] = root

        return root

    def draw(self) -> None:

        """Displays the phylogenetic tree.

        Only parental edges are shown, contributors are ignored."""

        G = nx.Graph()
        G.add_nodes_from(self.nodes.keys())

        queue = self.roots

        while len(queue):
            node = queue[0]
            queue = queue[1:]

            for c in node.children:
                G.add_edge(node.ID, c.ID)
                queue.append(c)

        pos = graphviz_layout(G, prog="dot")
        nx.draw_networkx(G, pos, labels={x.ID: x.model_parameters
                                         for x in self.nodes.values()})
        plt.show()
