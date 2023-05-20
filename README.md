# Code repository for "Less Bacon More Threshold"

This repository contains the code used to generate circuits, and collect sample statistics,
used in the paper "Less Bacon More Threshold".

## reproducing figures and statistics

Sitting next to this README, at the root of the repository,
are several scripts:
`step1_generate_circuits.sh`,
`step2_collect_stats.sh`
`step3_derive_fused_stats.sh`
and `step4_plots.sh`.
Most plots from the paper can be reproduced by setting up a python
environment and then running these scripts in order.
**You should tweak the collection script to customize the number
of worker processes to match your machine**.
You may also want to reduce the max shots and max errors,
since by default the collection script will take days to run
on a 96 core machine.

Assuming a linux-like system with a working python installation, and a bit of luck,
running the following bash code should in principle reproduce the results from the paper
after running for a few days:

```bash
# Preparation: make virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
sudo apt install parallel  # scripts use gnu-parallel to speed up circuit generation
pip install -r requirements.txt

./step1_generate_circuits.sh
./step2_collect_stats  # This one might take a week!
./step3_derive_fused_stats.sh
./step4_plot_stats
```

## directory structure

- `.`: top level of repository, with this README and the `step#` scripts
- `./tools`: tools for performing tasks such as generating circuits and plots
- `./src`: source root of the code; the directory to include in `PYTHONPATH`
- `./src/gen`: generic code for generating and debugging quantum error correction circuits using stim
- `./src/baconshor`: code for generating the bacon shor and fractal bacon shor circuits
- `./out`: Scripts are configured to create this directory and write their output to various locations within it.
