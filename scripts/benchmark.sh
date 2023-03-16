# !/bin/bash

for sliced_model in models/sliced_* ; do
    sliced_model_name=${sliced_model##*/}
    command="papdl benchmark ./$sliced_model -n $sliced_model_name -o models/benchmark_$sliced_model_name -b 10 -l 100 -r 10"
    echo "COMMAND: $command"
    eval $command
    papdl clean -B
done