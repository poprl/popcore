import unittest
from popcore.population import Population
import random

# Display libraries
import networkx as nx                                   # type: ignore
import matplotlib.pyplot as plt                         # type: ignore
from networkx.drawing.nx_pydot import graphviz_layout   # type: ignore


def draw(population: Population) -> None:  # TODO: Move that

    """Displays the phylogenetic tree.

    Only parental edges are shown, contributors are ignored."""

    G = nx.Graph()
    G.add_nodes_from(population.nodes.keys())

    queue = [population._root]

    while len(queue):
        node = queue[0]
        queue = queue[1:]

        for c in node.children:
            G.add_edge(node.id_str, c.id_str)
            queue.append(c)

    pos = graphviz_layout(G, prog="dot")
    nx.draw_networkx(G, pos, labels={x.id_str: x.model_parameters
                                     for x in population.nodes.values()})
    plt.show()


class TestPopulation(unittest.TestCase):

    def mutate(parent_parameters, hyperparameters, contributors=[]):
        new_DNA = list(parent_parameters)
        new_DNA[hyperparameters["spot"]] = hyperparameters["letter"]
        new_DNA = ''.join(new_DNA)
        return new_DNA, hyperparameters

    def test_visual_construction(self):
        # Visual test, uncomment the last line to see what the resulting trees
        # look like and check that they make sense.

        # Suppose this is a tree tracking the evolution of a
        # strand of DNA

        pop = Population()
        # tree.add_root("GGTCAACAAATCATAAAGATATTGG")  # Land snail DNA
        new_DNA = "OOOOO"
        pop.branch("Lineage 1")
        pop.branch("Lineage 2")
        pop.branch("Lineage 3")

        pop.checkout("Lineage 1")
        pop.commit(model_parameters=new_DNA)

        pop.checkout("Lineage 2")
        pop.commit(model_parameters=new_DNA)

        pop.checkout("Lineage 3")
        pop.commit(model_parameters=new_DNA)

        for _ in range(32):
            branch = random.choice(list(pop.branches))

            if branch == "_root":
                continue

            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            pop.checkout(branch)

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPopulation.mutate(pop.get_model_parameters(),
                                               hyperparameters)

            pop.commit(model_parameters=new_DNA,
                       hyperparameters=hyperparameters)

        # draw(pop)

    def test_linear(self):
        pop = Population()

        new_DNA = "OOOOO"
        DNA_history = [new_DNA]

        pop.commit(model_parameters=new_DNA)

        for x in range(16):
            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPopulation.mutate(new_DNA,
                                               hyperparameters)
            DNA_history.append(new_DNA)

            pop.commit(model_parameters=new_DNA,
                       hyperparameters=hyperparameters)

        # draw(pop)

        nbr_nodes = 1
        node = pop._root
        while len(node.children):
            nbr_nodes += 1
            assert len(node.children) == 1
            node = node.children[0]
            assert node.model_parameters == DNA_history[nbr_nodes-2]

        assert nbr_nodes == 18

    def test_nonlinear(self):
        pop = Population()
        pop.branch("b1")
        pop.checkout("b1")
        pop.commit("1")
        pop.branch("b2")
        pop.checkout("b2")
        pop.commit("2")
        pop.commit("3")
        pop.checkout("_root")
        pop.branch("b3")
        pop.checkout("b3")
        pop.commit("4")
        pop.checkout("b1")
        pop.commit("5")

        # draw(pop)

        pop.checkout('b2')
        self.assertSetEqual(set(pop.get_branches()),
                            set(["_root", "b1", "b2", "b3"]))
        self.assertEqual(len(pop.get_branches()), len(set(pop.get_branches())))

        self.assertEqual(pop.get_current_branch(), "b2")

        self.assertEqual(len(pop.get_commit_history()), 4)

    def test_detach(self):
        pop = Population()
        pop.branch("b1")
        pop.branch("b2")
        pop.checkout("b1")
        a = pop.commit(1)
        pop.commit(2)
        pop.checkout(a)
        pop.commit(3)
        pop.checkout("_root")
        pop.branch("b3")
        pop.checkout('b2')
        pop.commit(4)
        pop.commit(5)
        pop.commit(6)
        pop.branch("b4")
        pop.commit(7)
        pop.checkout("b4")
        pop.commit(8)
        pop.checkout("b3")
        a = pop.commit(9)
        b = pop.commit(15)
        pop.checkout(a)

        pop2 = pop.detach()
        pop2.branch("b1")
        pop2.checkout("b1")
        c = pop2.commit(10)
        pop2.commit(11)
        pop2.branch("b3")
        pop2.commit(12)
        pop2.checkout("b3")
        pop2.commit(13)
        pop2.checkout(pop2._root.id_str)
        d = pop2.commit(14)

        self.assertEqual(len(pop2.branches), 3)
        self.assertEqual(len(pop2.nodes), 8)

        self.assertEqual(len(pop.branches), 5)
        self.assertEqual(len(pop.nodes), 15)

        # draw(pop)
        # draw(pop2)

        pop.attach(pop2, auto_rehash=False)

        # draw(pop)

        self.assertEqual(len(pop.branches), 8)
        self.assertEqual(len(pop.nodes), 22)

        pop.checkout(a)
        self.assertListEqual(
            [x.id_str for x in pop.current_node.children], [b, c, d])
