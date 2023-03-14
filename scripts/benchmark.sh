# !/bin/bash

for sliced_model in models/sliced_* ; do
    sliced_model_name=${sliced_model##*/}
    echo "COMMAND: papdl benchmark ./$sliced_model -n $sliced_model_name -o models/benchmark_$sliced_model_name -b 10 -l 100"
    papdl benchmark ./$sliced_model -n $sliced_model_name -o "models/benchmark_$sliced_model_name"
    papdl clean -B
done