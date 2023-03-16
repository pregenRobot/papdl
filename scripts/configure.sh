# !/bin/bash

for benchmark_path in models/benchmark_* ; do
    benchmark_name=${benchmark_path##*/}
    command="papdl configure $benchmark_path -o ./models/configured_$benchmark_name iot0g49yoi6ezxfy9uy4h0o16 203511" 
    echo "COMMAND: $command"
    eval $command
done