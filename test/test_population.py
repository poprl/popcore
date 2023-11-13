import unittest
from popcore.core import Population
from popcore.iterators import lineage
import random
from .fixtures import (random_linear_dna_evolution, nonlinear_population,
                         detach_from_pop)


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

            if branch == "main":
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
        pop, DNA_history = random_linear_dna_evolution()

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
        pop = nonlinear_population()

        pop.checkout('b2')
        self.assertSetEqual(pop.branches(),
                            set(["main", "b1", "b2", "b3"]))
        self.assertEqual(len(pop.branches()), len(pop.branches()))

        self.assertEqual(pop.branch(), "b2")

        self.assertEqual(len([x for x in lineage(pop)]), 3)

    def test_detach(self):
        """This tests the correctness of the detach/attach operations"""
        pop, pop2, a, b, c, d, = detach_from_pop()

        self.assertEqual(len(pop2.branches()), 3)
        self.assertEqual(len(pop2._nodes), 9)

        self.assertEqual(len(pop.branches()), 5)
        self.assertEqual(len(pop._nodes), 16)

        # draw(pop)
        # draw(pop2)

        pop.attach(pop2)

        self.assertEqual(len(pop.branches()), 8)
        self.assertEqual(len(pop._nodes), 24)

        pop.checkout(a)
        self.assertListEqual(
            [x.name for x in pop._player.descendants], [b, c, d])
