# !/bin/bash

for configuration_path in models/configuration_* ; do
    confugration_name = ${configuration_path}
    command="papdl deploy $configuration_path"
done