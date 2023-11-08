import unittest
from popcore.core import Population
from popcore.iterators import lineage
import random

from popcore import Population


class TestPopulation(unittest.TestCase):

    def mutate(parent_parameters, hyperparameters, contributors=[]):
        """Mutate a strand of DNA (replace a character in the str at random)"""
        new_DNA = list(parent_parameters)
        new_DNA[hyperparameters["spot"]] = hyperparameters["letter"]
        new_DNA = ''.join(new_DNA)
        return new_DNA, hyperparameters

    def test_visual_construction(self):
        """Tree tracking the evolution of a strand of DNA along 3 evolutionary
        paths"""
        # Visual test, uncomment the last line to see what the resulting trees
        # look like and check that they make sense.

        pop = Population()
        # tree.add_root("GGTCAACAAATCATAAAGATATTGG")  # Land snail DNA
        new_DNA = "OOOOO"
        pop.branch("Lineage 1")
        pop.branch("Lineage 2")
        pop.branch("Lineage 3")

        pop.checkout("Lineage 1")
        pop.commit(parameters=new_DNA)

        pop.checkout("Lineage 2")
        pop.commit(parameters=new_DNA)

        pop.checkout("Lineage 3")
        pop.commit(parameters=new_DNA)

        for _ in range(32):
            branch = random.choice(list(pop.branches()))

            if branch == "_root":
                continue

            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            pop.checkout(branch)

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPopulation.mutate(pop._player.parameters,
                                               hyperparameters)

            pop.commit(parameters=new_DNA,
                       hyperparameters=hyperparameters)

    def test_linear(self):
        """This tests the correctness of the case where the population consists
        of only a single lineage"""
        pop = Population()

        new_DNA = "OOOOO"
        DNA_history = [new_DNA]

        pop.commit(parameters=new_DNA)

        for x in range(16):
            letter = random.choice("ACGT")
            spot = random.randrange(len(new_DNA))

            hyperparameters = {"letter": letter, "spot": spot}
            new_DNA, _ = TestPopulation.mutate(new_DNA,
                                               hyperparameters)
            DNA_history.append(new_DNA)

            pop.commit(parameters=new_DNA,
                       hyperparameters=hyperparameters)

        nbr_nodes = 1
        node = pop._root
        while len(node.descendants):
            nbr_nodes += 1
            assert len(node.descendants) == 1
            node = node.descendants[0]
            assert node.parameters == DNA_history[nbr_nodes-2]

        assert nbr_nodes == 18

    def test_nonlinear(self):
        """This tests the case where the population has multiple branches at
        different generations"""
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
        self.assertSetEqual(pop.branches(),
                            set(["_root", "b1", "b2", "b3"]))
        self.assertEqual(len(pop.branches()), len(pop.branches()))

        self.assertEqual(pop.branch(), "b2")

        self.assertEqual(len([x for x in lineage(pop)]), 3)

    def test_detach(self):
        """This tests the correctness of the detach/attach operations"""
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
        pop2.checkout(pop2._root.name)
        d = pop2.commit(14)

        self.assertEqual(len(pop2.branches()), 3)
        self.assertEqual(len(pop2._nodes), 8)

        self.assertEqual(len(pop.branches()), 5)
        self.assertEqual(len(pop._nodes), 15)

        # draw(pop)
        # draw(pop2)

        pop.attach(pop2, auto_rehash=False)

        self.assertEqual(len(pop.branches()), 8)
        self.assertEqual(len(pop._nodes), 22)

        pop.checkout(a)
        self.assertListEqual(
            [x.name for x in pop._player.descendants], [b, c, d])
