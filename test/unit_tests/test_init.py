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
        self.assertEqual(len(pop._generations), 1)
        self.assertEqual(len(pop._generations[0]), 0)
        self.assertIsNone(pop._player.parameters)
        self.assertIsNone(pop._player.hyperparameters)
        self.assertIsNone(pop._player.interaction)
        self.assertEqual(pop._player.timestep, 1)
        self.assertEqual(pop._branches, set(["main"]))
        self.assertEqual(len(pop._nodes), 2)

    def test_no_args(self):
        pop = Population()

        self.assertEqual(pop._nodes["_root"], pop._root)
        self.assertEqual(pop._nodes["_root"], pop._player)
        self.assertEqual(pop._player.name, "_root")
        self.assertIsNone(pop._stage_dir)
        self.assert_invariants(pop)

    def test_with_root_name(self):
        pop = Population(root_name="root beer")

        self.assertEqual(pop._nodes["root beer"], pop._root)
        self.assertEqual(pop._nodes["root beer"], pop._player)
        self.assertEqual(pop._player.name, "root beer")
        self.assertIsNone(pop._stage_dir)
        self.assert_invariants(pop)

    def test_with_stage_dir(self):
        pop = Population(stage_dir="here")

        self.assertEqual(pop._nodes["_root"], pop._root)
        self.assertEqual(pop._nodes["_root"], pop._player)
        self.assertEqual(pop._player.name, "_root")
        self.assertEqual(pop._stage_dir, "here/.pop/")
        self.assert_invariants(pop)

    def test_pre_commit_hooks(self):
        pass
        # TODO

    def test_post_commit_hooks(self):
        pass
        # TODO

    def test_save_hooks(self):
        pass
        # TODO

    def test_load_hooks(self):
        pass
        # TODO
