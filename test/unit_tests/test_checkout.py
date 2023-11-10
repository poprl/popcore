import unittest
from popcore.core import Population


class TestBranch(unittest.TestCase):
    def assert_invariants(self, pop):
        """Properties that should be invariant under any arguments"""
        self.assertEqual(pop._player.branch, "main")
        self.assertIsNone(pop._player.parent)
        self.assertEqual(pop._player, pop._root)
        self.assertEqual(pop._nodes["main"], pop._player)
        self.assertEqual(pop._nodes["_root"], pop._root)
        self.assertEqual(pop._nodes["_root"], pop._player)
        self.assertEqual(len(pop._generations), 1)
        self.assertEqual(len(pop._generations[0]), 0)
        self.assertIsNone(pop._player.parameters)
        self.assertIsNone(pop._player.hyperparameters)
        self.assertIsNone(pop._player.interaction)
        self.assertEqual(pop._player.timestep, 1)
        self.assertEqual(pop._player.name, '_root')
        self.assertEqual(pop._branches, set(["main", "b1"]))
        self.assertEqual(len(pop._nodes), 3)

    def test_checkout_current_branch(self):
        pop = Population()
        pop.branch("b1")
        pop.checkout("main")

        self.assertEqual(pop._branch, "main")
        self.assert_invariants(pop)

    def test_checkout_new_branch(self):
        pop = Population()
        pop.branch("b1")
        pop.checkout("b1")

        self.assertEqual(pop._branch, "b1")
        self.assert_invariants(pop)

    def test_checkout_branch_that_does_not_exist(self):
        pop = Population()
        pop.branch("b1")

        self.assertRaises(ValueError, pop.checkout, "b2")
