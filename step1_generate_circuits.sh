#!/bin/bash

set -e

PYTHONPATH=src parallel --ungroup tools/gen_circuits \
     --out_dir out/circuits \
     --diameter 5 \
     --rounds "3" \
     --noise_model uniform \
     --noise_strength {1} \
     --style bacon_shor_xx_surgery \
     --b {2} \
     ::: 1e-6 2e-6 3e-6 5e-6 7e-6 1e-5 2e-5 3e-5 5e-5 7e-5 1e-4 2e-4 3e-4 5e-4 7e-4 1e-3 2e-3 3e-3 5e-3 7e-3 1e-2 2e-2 3e-2 5e-2 7e-2 1e-1 \
     ::: X Z

PYTHONPATH=src parallel --ungroup tools/gen_circuits \
    --out_dir out/circuits \
    --diameter {1} \
    --rounds "d*4" \
    --noise_model uniform \
    --noise_strength {2} \
    --style {3} \
    --b {4} \
    --fractal_pitch {5} \
    --surgery_hold_factor 1 \
    ::: {2..43} \
    ::: 1e-3 \
    ::: fractal_bacon_shor \
    ::: X Z \
    ::: 5 7 9

PYTHONPATH=src parallel --ungroup tools/gen_circuits \
    --out_dir out/circuits \
    --diameter {1} \
    --rounds "d*4" \
    --noise_model uniform \
    --noise_strength {2} \
    --style {3} \
    --b {4} \
    --fractal_pitch {5} \
    --surgery_hold_factor {5} \
    ::: {2..43} \
    ::: 1e-3 \
    ::: fractal_bacon_shor \
    ::: X Z \
    ::: 5 7 9

PYTHONPATH=src parallel --ungroup tools/gen_circuits \
    --out_dir out/circuits \
    --diameter {1} \
    --rounds "d*4" \
    --noise_model uniform \
    --noise_strength {2} \
    --style {3} \
    --b {4} \
    ::: {2..43} \
    ::: 1e-3 \
    ::: bacon_shor \
    ::: X Z \
    ::: 3 5 7 9
