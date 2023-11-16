import unittest
from popcore.core import Player
from popcore.storage.repo import Repository


class TestRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.repo = Repository(
            stage=".poprl/", filesystem='file'
        )

    def test_directory_structure_over_file(self):

        self.assertTrue(
            self.repo.filesystem.exists('.poprl/')
        )
        self.assertTrue(
            self.repo.filesystem.isdir('.poprl/'))
        self.assertTrue(
            self.repo.filesystem.exists(self.repo.structure.index)
        )
        self.assertTrue(
            self.repo.filesystem.exists(self.repo.structure.gen)
        )
        self.assertTrue(
            self.repo.filesystem.exists(self.repo.structure.branches)
        )

    def test_write_player_to_index(self):
        self.repo.commit(
            "root",
            Player(name="root")
        )

    def tearDown(self) -> None:
        self.repo.remove()
