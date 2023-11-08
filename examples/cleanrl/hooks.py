
from typing import Any
import os
import torch

from popcore import Player, Population
from popcore.hooks import PostCommitHook


class PersitenceHook(PostCommitHook):

    def __init__(
        self,
        outdir: str
    ) -> None:
        super().__init__()
        self._outdir = outdir
        os.makedirs(outdir, exist_ok=True)

    def _post(
        self, population: Population, player: Player,
        *args: Any, **kwds: Any
    ):
        """
            Save Agent and Optimizer state
        """
        torch.save(
            {
                'agent': player.parameters['agent'].state_dict(),
                'optimizer': player.parameters['optimizer'].state_dict()
            },
            os.path.join(self._outdir, player.name)
        )
        return player
