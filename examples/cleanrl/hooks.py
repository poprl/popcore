
from typing import Any, Dict
import os
import torch

from popcore import Player, Population, Interaction
from popcore.hooks import PostCommitHook


class PersitenceHook(PostCommitHook):

    def __init__(
        self,
        save_every: int
    ) -> None:
        super().__init__()
        self._save_every = save_every

    def _post(
        self, population: Population, player: Player,
        interaction: Interaction, timestep: int, parameters: Dict[str, Any]
    ):
        """
            Save Agent and Optimizer state
        """
        if timestep % self._save_every == 0:
            path = os.path.join(population.stage(), player.name)
            torch.save(
                {
                    'agent': parameters['agent'].state_dict(),
                    'optimizer': parameters['optimizer'].state_dict()
                },
                path
            )
            player.persisted = path
        return player
