#!/bin/bash

set -e

mkdir -p out/

sinter plot \
    --in out/fused_stats.csv \
    --xaxis "Grid Diameter (d)" \
    --x_func "metadata['d']" \
    --group_func "f'''Normal Bacon Shor Code''' if 'fractal' not in metadata['c'] else f'''fractal_pitch={metadata['fractal_pitch']} surgery_hold_factor={metadata['surgery_hold_factor']}'''" \
    --plot_args_func "{'linewidth': 4} if 'fractal' not in metadata['c'] else {}" \
    --title "Logical Error Rate of Bacon Shor Code per Round vs Grid Diameter" \
    --subtitle "basis=fused XZ, rounds=4d, noise=uniform, p=0.001" \
    --failure_unit_name "round" \
    --failure_units_per_shot_func "metadata['r']" \
    --failure_values_func "2" \
    --out "out/error_rate_xz.png" \
    --filter_func "metadata['p'] == 0.001 and metadata['noise'] == 'uniform' and metadata['b'] == 'XZ' and metadata['r'] == metadata['d'] * 4 and metadata.get('surgery_hold_factor', 1) == 1" \
    && echo "wrote file://$(pwd)/out/error_rate_xz.png" &


sinter plot \
    --in out/stats.csv \
    --xaxis "Grid Diameter (d)" \
    --x_func "metadata['d']" \
    --group_func "f'''Normal Bacon Shor Code''' if 'fractal' not in metadata['c'] else f'''fractal_pitch={metadata['fractal_pitch']} surgery_hold_factor={metadata['surgery_hold_factor']}'''" \
    --plot_args_func "{'linewidth': 4} if 'fractal' not in metadata['c'] else {}" \
    --title "Logical Error Rate of Bacon Shor Code per Round vs Grid Diameter" \
    --subtitle "basis=X, rounds=4d, noise=uniform, p=0.001" \
    --failure_unit_name "round" \
    --failure_units_per_shot_func "metadata['r']" \
    --out "out/error_rate_x.png" \
    --filter_func "metadata['p'] == 0.001 and metadata['noise'] == 'uniform' and metadata['b'] == 'X' and metadata['r'] == metadata['d'] * 4" \
    && echo "wrote file://$(pwd)/out/error_rate_x.png" &


sinter plot \
    --in out/stats.csv \
    --xaxis "Grid Diameter (d)" \
    --x_func "metadata['d']" \
    --group_func "f'''Normal Bacon Shor Code''' if 'fractal' not in metadata['c'] else f'''fractal_pitch={metadata['fractal_pitch']} surgery_hold_factor={metadata['surgery_hold_factor']}'''" \
    --plot_args_func "{'linewidth': 4} if 'fractal' not in metadata['c'] else {}" \
    --title "Logical Error Rate of Bacon Shor Code per Round vs Grid Diameter" \
    --subtitle "basis=Z, rounds=4d, noise=uniform, p=0.001" \
    --failure_unit_name "round" \
    --failure_units_per_shot_func "metadata['r']" \
    --filter_func "metadata['p'] == 0.001 and metadata['noise'] == 'uniform' and metadata['b'] == 'Z' and metadata['r'] == metadata['d'] * 4" \
    --out "out/error_rate_z.png" \
    && echo "wrote file://$(pwd)/out/error_rate_z.png" &

sinter plot \
    --in out/stats.csv out/fused_stats.csv \
    --x_func "metadata['p']" \
    --group_func "'data init/measure=X [checks X1->X1, X2->X2, XX->+-1]' if metadata['b'] == 'X' else 'data init/measure=Z [checks ZZ->ZZ]' if metadata['b'] == 'Z' else 'total combined error'" \
    --subtitle "{common}" \
    --xaxis "[log]Noise Strength" \
    --title "Logical Error Rate of Lattice Surgery" \
    --out "out/error_rate_xx_surgery.png" \
    --filter_func "metadata['c'] == 'bacon_shor_xx_surgery'" \
    && echo "wrote file://$(pwd)/out/error_rate_xx_surgery.png" &

wait
