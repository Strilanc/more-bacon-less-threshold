import stim

from gen._noise import NoiseRule
from gen._circuit_util import (
    make_phenomenological_circuit_for_stabilizer_code,
    make_code_capacity_circuit_for_stabilizer_code,
)
from gen._flow import PauliString
from gen._patch import Patch


class StabilizerCode:
    def __init__(self, patch: Patch, obs_x: PauliString, obs_z: PauliString):
        self.patch = patch
        self.obs_x = obs_x
        self.obs_z = obs_z

    def make_code_capacity_circuit(
            self,
            *,
            noise: NoiseRule,
            basis: str,
    ) -> stim.Circuit:
        assert noise.flip_result == 0
        return make_code_capacity_circuit_for_stabilizer_code(
            patch=self.patch,
            noise=noise,
            basis=basis,
            obs_x=self.obs_x,
            obs_z=self.obs_z,
        )

    def make_phenomenological_circuit(
            self,
            *,
            noise: NoiseRule,
            rounds: int,
            basis: str,
    ) -> stim.Circuit:
        return make_phenomenological_circuit_for_stabilizer_code(
            patch=self.patch,
            noise=noise,
            rounds=rounds,
            basis=basis,
            obs_x=self.obs_x,
            obs_z=self.obs_z,
        )
