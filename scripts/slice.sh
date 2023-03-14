# !/bin/bash

for model_path in models/* ; do
    model_name=${model_path##*/}
    echo "COMMAND: papdl slice $model_path -o ./models/sliced_$model_name"
    papdl slice $model_path -o "./models/sliced_$model_name"
done
