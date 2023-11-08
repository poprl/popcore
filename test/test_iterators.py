import unittest
from popcore.core import Population
from popcore.iterators import lineage, generation, flatten
import random


class TestIterators(unittest.TestCase):

    def mutate(parent_parameters, hyperparameters, contributors=[]):
        """Mutate a strand of DNA (replace a character in the str at random)"""
        new_DNA = list(parent_parameters)
        new_DNA[hyperparameters["spot"]] = hyperparameters["letter"]
        new_DNA = ''.join(new_DNA)
        return new_DNA, hyperparameters

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
            new_DNA, _ = TestIterators.mutate(new_DNA,
                                              hyperparameters)
            DNA_history.append(new_DNA)

            pop.commit(parameters=new_DNA, hyperparameters=hyperparameters)

        # Test lineage
        self.assertEqual(len([x for x in lineage(pop)]), 17)

        node = pop._player
        iterator = lineage(pop)
        while node.parent:
            self.assertEqual(next(iterator), node)
            node = node.parent

        # Test flatten
        self.assertEqual(len([x for x in flatten(pop)]),
                         len(set([x for x in flatten(pop)])))
        self.assertEqual(len([x for x in flatten(pop)]), 17)

        # Test generation
        for x in range(1, 18):
            self.assertEqual(len([y for y in generation(pop, x)]), 1)

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

        # from popcore.utils import draw
        # draw(pop)

        pop.checkout('b2')

        # lineage
        self.assertEqual(len([x for x in lineage(pop)]), 3)
        self.assertEqual(len([x for x in lineage(pop, "b1")]), 2)

        # Test flatten
        self.assertEqual(len([x for x in flatten(pop)]),
                         len(set([x for x in flatten(pop)])))
        self.assertEqual(len(set([x for x in flatten(pop)])), 5)

        # Test generation
        self.assertEqual(len([x for x in generation(pop, 1)]), 2)
        self.assertEqual(len([x for x in generation(pop, 2)]), 2)
        self.assertEqual(len([x for x in generation(pop)]), 1)

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
        pop.commit(15)
        pop.checkout(a)

        pop2 = pop.detach()
        pop2.branch("b1")
        pop2.checkout("b1")
        pop2.commit(10)
        pop2.commit(11)
        pop2.branch("b3")
        pop2.commit(12)
        pop2.checkout("b3")
        pop2.commit(13)
        pop2.checkout(pop2._root.name)
        pop2.commit(14)

        # lineage
        self.assertEqual(len([x for x in lineage(pop2)]), 1)
        self.assertEqual(len([x for x in lineage(pop2, "b1")]), 3)

        # Test flatten
        self.assertEqual(len([x for x in flatten(pop2)]),
                         len(set([x for x in flatten(pop2)])))
        self.assertEqual(len(set([x for x in flatten(pop2)])), 5)

        # Test generation
        self.assertEqual(len([x for x in generation(pop2, 1)]), 2)
        self.assertEqual(len([x for x in generation(pop2, -2)]), 1)
        self.assertEqual(len([x for x in generation(pop2)]), 2)

        # draw(pop)
        # draw(pop2)

        pop.attach(pop2)

        # lineage
        self.assertEqual(len([x for x in lineage(pop)]), 1)
        self.assertEqual(len([x for x in lineage(pop, "b1")]), 2)
        self.assertEqual(len([x for x in lineage(pop, "b11")]), 4)

        # Test flatten
        self.assertEqual(len([x for x in flatten(pop)]),
                         len(set([x for x in flatten(pop)])))
        self.assertEqual(len(set([x for x in flatten(pop)])), 15)

        # Test generation
        self.assertEqual(len([x for x in generation(pop, 1)]), 3)
        self.assertEqual(len([x for x in generation(pop, 2)]), 6)
        self.assertEqual(len([x for x in generation(pop, -2)]), 2)
        self.assertEqual(len([x for x in generation(pop)]), 4)
