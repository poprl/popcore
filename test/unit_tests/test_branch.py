import unittest
from popcore.core import Population


class TestBranch(unittest.TestCase):
    def assert_invariants(self, pop):
        """Properties that should be invariant under any arguments"""
        self.assertEqual(pop._player.branch, "main")
        self.assertEqual(pop._branch, "main")
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

    def test_no_args(self):
        pop = Population()
        b = pop.branch()

        self.assertEqual(b, "main")
        self.assertEqual(pop._branches, set(["main"]))
        self.assertEqual(len(pop._nodes), 2)
        self.assert_invariants(pop)

    def test_with_name(self):
        pop = Population()
        b = pop.branch("branch1")

        self.assertEqual(b, "branch1")
        self.assertEqual(pop._branches, set(["main", "branch1"]))
        self.assertEqual(len(pop._nodes), 3)
        self.assert_invariants(pop)

    def test_same_name_twice(self):
        pop = Population()
        pop.branch("branch1")
        self.assertRaises(ValueError, pop.branch, "branch1")

    def test_illegal_name_main(self):
        pop = Population()
        self.assertRaises(ValueError, pop.branch, "main")

    def test_conflict_with_commit_name(self):
        pop = Population()
        self.assertRaises(ValueError, pop.branch, "_root")

    def test_auto_name(self):
        pass
        # TODO: Auto_name feature not implemented
