# papdl - Plug and Play Deep Learning

### User Workflow Goals

#### (1) (Design) Users should be able to design a DNN
  - Define the structure of the network
  - Define the parameters for each layer of the network

Implementation: 
- Users define a keras model.
- Users use `keras.save()`  to save the model to the local directory.
The keras model definition is already "plug-and-play" in the sense that users import available model definitions and make a pipeline (represented as an array)

#### (2) (Build) Users should be able to package up the  the DNN design
  - PAPDL should be able to parse a keras model description
    - Parse network strucutre
    - Parse parameters for each layers
  - PAPDL should be able to slice up the network into individual layers
  - PAPDL should be able to identify the container image for each layer
  - PAPDL should bundle up network structure, network parameters, and initialized weights into a single folder than can be shared
  - Users should be able to share these bundles 

Implementation:
- Users run a command to load a model saved with `keras.save()`.
- PAPDL slices up the network using Scission into `keras.functional.Function` objects.
- PAPDL prepares a set of Dockerfiles for building containers for running a specific slices of the network.
- PAPDL identifies the Dockerfiles necessary for building the layers and generates a `docker-compose.yml` file containing all the necessary services to run the network.
- PAPDL should generate a folder and place the docker-compose.yml file along with initialized weights for each layer in the network
- Folder can be tar-balled and shared.

#### (3) (Prediction) Users should be able to run inference operations on the DNN
- Users should be able to upload prediction target to the DNN cluster
- Users should be able to perform prediction on the uploaded data
- Users should be able to shut down the distributed DNN

Implementation:
- A single command is exectued (`docker-compose up`) to launch all the necessary services
- Send a request to the orchestrator service to upload the prediction target data
- Send a request to the orchestrator service to start a prediction operation
- A single command is executed (`docker-compose down`) to shut down all the services

(5) (Train) Users should be able to run training operations on the DNN

- Users should be able to upload prediction target to the DNN cluster
- Users should be able to upload a configuration file detailing the training methodology (Optimizer, Loss Function, Epochs, etc.)
- Users should be able to start a training process on the uploaded data
- Users should be able to download the training model back to their local machine
- Users should be able to shut down the distributed DNN

Implementation:
- A single command is executed (`docker-compose up`) to launch all the necessary services
- Send a request to the orchestrator service to upload the training data
- Send a request to the orchestrator service to upload the training configuration
- Send a request to the orchestrator service to start the training operation based on the uploaded config file and training data
- Send a request to the orchestrator to fetch the latest model weights
- A single command is executed (`docker-compose down`) to shut down the cluster


### Goal Usage example

(1)

```sh
$ cat model_description.py
...
model = keras.Sequential(
  [
    keras.Input(shape=input_shape),
    layers.Conv2D(32, kernel_size=(3,3), activation="relu"),
    layers.MaxPoolign2D(pool_size=(2,2)),
    layers.Conv2D(64, kernel_size=(3,3), activation="relu"),
    layers.MaxPoolign2D(pool_size=(2,2))
    ...
  ]
)
model.save("mnist_classifier_model_description")
...
```

(2)

```sh
$ papdl --generate mnist_classifier_model_description --out mnist_papdl
```

(3)

```sh
$ cd mnist_papdl
$ docker-compose up
```

(4 - inference)

```
$ curl -Xs POST --data inference_data.tar http://orchestrator-service
$ curl 
```


-------------------------------------------------

### GOAL Example usage

```python
$ cat model_description.py
...
model = keras.Sequential(
  [
    keras.Input(shape=input_shape),
    layers.Conv2D(32, kernel_size=(3,3), activation="relu"),
    layers.MaxPoolign2D(pool_size=(2,2)),
    layers.Conv2D(64, kernel_size=(3,3), activation="relu"),
    layers.MaxPoolign2D(pool_size=(2,2))
    ...
  ]
)
model.save("mnist_classifier_model_description")
...

$ tree mnist_classifier_model_description
- minist_classifier_model_description/
  - variables/
    - variables.index
    - variables.data-00001-of-0002
    ...
  - saved_model.pb


## GENERATE docker-compose.yml and initialized weights directory
$ papdl --generate --path mnist_classifier_model_description


# Stores the structure and arguments for the network
$ cat docker-compose.yml
services:
  conv2d-8743b52063cd84097a65d1633f5c74f5:
    build: papdl/blocks/layers/Conv2D ## BUILD off of defined dockerfiles
    environment:
      - INPUT_SHAPE=32
      - KERNEL_SIZE=(3,3)
      - ACTIVATION="relu"
    ...
  maxpooling2d-c898896f3f70f61bc3fb19bef222aa860e5ea717:
    build: papdl/blocks/layers/MaxPooling2D
    environment:
      - POOL_SIZE=(2,2)
    ...
  conv2d-4dd8965d1d476fa0d026722989a6b772:
    build: papdl/blocks/layers/Conv2D
    environment:
      - INPUT_SHAPE=64
      - KERNEL_SIZE=(3,3)
      - activation="relu"
    ...
  maxpooling2d-a936af92b0ae20b1ff6c3347a72e5fbe:
    build: papdl/blocks/layers/MaxPooling2D
    environment:
      - POOL_SIZE=(2,2)
    ...
  ...
  orchestrator:
    build: papdl/blocks/core/Orchestrator
    environment:
```


Low level Description

(1) (Design) Create a DNN **structure** by stacking up slices
  - Load a Keras model onto memory - Keras
  - Parse Keras model structure - Keras
  - Fetch slices of the network - Scission
  - Identify the relevant containers necessary to run each slice - PAPDL
    - Create a set of containers for running a specific type of slice
    - Create a one-to-one mapping between a Keras slice and container

(2) (Configure) Set **parameter** values for each slice
  - Load a Keras model onto memory - Keras
  - Parse Keras model structure - Keras
  - Fetch slices of the network - Scission
  - Identify the parameters for each slice - PAPDL
    - Identify weights
    - Identify input and output dims
    - Identify slice-specific params (ex: kernel size for Conv2D, rate for Dropout, etc.)

## End User Workflow

User goal
- Design a DNN in a plug-and-play fashion
  - Design the architecture of the network (ordering of layers)
    - Load a Keras DNN model and slice the networks where possible
      - (1) Load Keras model
      - (2) Use Scission to slice up network
      - (3) Identify the 
  - Assign parameters of components of the network
    - Load a Keras DNN model and interpret the parameters of each slice of the network
- Run the DNN over a distributed collection of compute resources
  - Run the containers as FaaS-like services