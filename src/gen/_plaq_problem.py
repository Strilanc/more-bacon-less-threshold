import math
import pathlib
import sys
from typing import Union, Optional, Iterable, Dict, Any, Callable

import numpy as np
import sinter
import stim

from gen._noise import occurs_in_classical_control_system
from gen._patch import Patch
from gen._util import stim_circuit_with_transformed_coords


class PlaqProblem:
    """A decoding problem. A sinter.Task with additional debugging info."""

    def __init__(self,
                 *,
                 noisy_circuit: stim.Circuit,
                 error_model_for_decoder: Optional[stim.DetectorErrorModel] = None,
                 layouts: Iterable[Patch],
                 json_metadata: Optional[Dict[str, Any]] = None,
                 postselect_marked_detectors: bool = False):
        """
        Args:
            noisy_circuit: The noisy circuit containing logical observables to
                error correct via detectors.
            error_model_for_decoder: Defaults to None. Overrides the dem given
                to the decoder (instead of using the one automatically extracted
                from the circuit by stim).
            layouts: A list of stabilizer configurations used during the
                problem.
            json_metadata: Metadata included when sampling with sinter.
            postselect_marked_detectors: If true, any detector that has a 4th coordinate
                not equal to 0 will be postselected.
        """
        self.noisy_circuit = noisy_circuit
        self.error_model_for_decoder = error_model_for_decoder
        self.layouts = tuple(layouts)
        self.json_metadata = json_metadata
        self.postselect_marked_detectors = postselect_marked_detectors

    def after_coordinate_transform(self, coord_transform: Callable[[complex], complex]) -> 'PlaqProblem':
        assert self.error_model_for_decoder is None, "Not Implemented"
        return PlaqProblem(
            noisy_circuit=stim_circuit_with_transformed_coords(self.noisy_circuit, coord_transform),
            error_model_for_decoder=None,
            layouts=[e.after_coordinate_transform(coord_transform) for e in self.layouts],
            json_metadata=self.json_metadata,
            postselect_marked_detectors=self.postselect_marked_detectors,
        )

    def _postselection_mask(self) -> Optional[np.ndarray]:
        if not self.postselect_marked_detectors:
            return None
        n = self.noisy_circuit.num_detectors + self.noisy_circuit.num_observables
        mask = np.zeros(shape=math.ceil(n / 8), dtype=np.uint8)
        for k, coord in self.noisy_circuit.get_detector_coordinates().items():
            if len(coord) >= 4 and coord[3]:
                mask[k // 8] |= 1 << (k % 8)
        return mask

    def to_sinter_task(self, *, decoder: Optional[str] = None) -> sinter.Task:
        return sinter.Task(
            circuit=self.noisy_circuit,
            decoder=decoder,
            detector_error_model=self.error_model_for_decoder,
            json_metadata=self.json_metadata,
            postselection_mask=self._postselection_mask(),
        )

    def write_debug_files(self,
                          out_dir: Union[str, pathlib.Path],
                          *,
                          known_error: Optional[Iterable[stim.ExplainedError]] = None) -> None:
        def _print_wrote(written_path: pathlib.Path) -> None:
            text = str(written_path).replace('\\', '/')
            print(f"wrote file://{text}")

        out_dir = pathlib.Path(out_dir).absolute()
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "stabilizer_configurations.svg"
        with open(path, "w") as f:
            from synth import viz
            print(viz.plaq_plans_svg_viewer(self.layouts), file=f)
        _print_wrote(path)

        path = out_dir / "circuit.stim"
        with open(path, "w") as f:
            print(self.noisy_circuit.without_noise(), file=f)
        _print_wrote(path)

        path = out_dir / "noisy_circuit.stim"
        with open(path, "w") as f:
            print(self.noisy_circuit, file=f)
        _print_wrote(path)

        path = out_dir / "circuit_layers.html"
        with open(path, 'w') as f:
            from synth import viz
            print(viz.stim_circuit_html_viewer(
                self.noisy_circuit,
                stabilizer_config=self.layouts[0] if self.layouts else None,
                width=500,
                height=800,
                known_error=known_error,
            ), file=f)
        _print_wrote(path)

        path = out_dir / "model.dem"
        det_model = self.error_model_for_decoder
        if det_model is None:
            det_model = self.noisy_circuit.detector_error_model(decompose_errors=True)
        with open(path, "w") as f:
            print(det_model, file=f)
        _print_wrote(path)

        kept = stim.Circuit()
        for instruction in self.noisy_circuit.without_noise():
            if isinstance(instruction, stim.CircuitInstruction):
                if instruction.name in ["MPP", "DETECTOR", "OBSERVABLE_INCLUDE", "SHIFT_COORDS"]:
                    continue
                if occurs_in_classical_control_system(instruction):
                    continue
            kept.append(instruction)
        try:
            import stimcirq
            cirq_circuit = stimcirq.stim_circuit_to_cirq_circuit(kept)
            import cirq_web
            path = out_dir / "circuit_viewer.html"
            cirq_web.Circuit3D(cirq_circuit).generate_html_file(file_name=str(path))
            _print_wrote(path)
        except NotImplementedError as ex:
            print(ex, file=sys.stderr)
            print("Failed to write 3d viewer. Ignoring exception and continuing.", file=sys.stderr)
