
for configured_model in models/configured_benchmark_b$1_* ; do
    configured_model_name=${configured_model}
    papdl clean -S -O
    command="papdl deploy $configured_model"
    echo "COMMAND: $command"
    eval $command

    ssh vm4 curl localhost:8765/connect
    ssh vm4 curl localhost:8765/activate
    ssh vm4 curl --request POST --data '{"\""batch_size"\"":1,\"iterations\":1}' localhost:8765/benchmark

    echo $result
    exit 0
    # papdl clean -S -O
done