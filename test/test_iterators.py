import unittest
from popcore.iterators import lineage, generation, flatten
from .situations import (random_linear_dna_evolution, nonlinear_population,
                         detach_from_pop)


class TestIterators(unittest.TestCase):

    def test_linear(self):
        """This tests the correctness of the case where the population consists
        of only a single lineage"""
        pop, _ = random_linear_dna_evolution()

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
        pop = nonlinear_population()

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
        pop, pop2, _, _, _, _ = detach_from_pop()

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
