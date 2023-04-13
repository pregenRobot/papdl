
# PAPDL - Making Distributed Model Deployment Easier

Distributed systems and edge computing have become increasingly important due to the rapid growth of data generated and the demand for scalable computer systems. In parallel to this growth, Deep Neural Networks have shown exceptional results in a variety of tasks to be performed on the data from image recognition to video processing. PAPDL is a command line program that addresses the challenges of Deep Neural Network (DNN) predictions on real-time streaming data. The proposed program aims to decouple DNN layers from the original model, encapsulate them using containerized services, and deploy them across of set of distributed systems. The decoupling operation takes resource utilization metrics for executing a DNN layer into account in order to prevent certain devices from being overloaded and also aims to minimize the latency for getting a prediction for a given input. PAPDL can orchestrate services running across the distributed system to perform prediction that is semantically equivalent to running the entire model as a monolithic architecture on a single device.

## Requirements and Installation

1. Install Docker https://docs.docker.com/get-docker/
2. Install PAPDL `pip3 install papdl`


## Usage

### 1. Prepare a set of devices which can communicate with each other within a local network or over the internet.

This example will show a practical use case of optimally deploying a VGG16 Image classification model across a Docker Swarm. We will be using the following devices to run the model:

| Device Name | CPU Cores | Arch    | Memory | Swap |
|-------------|-----------|---------|--------|------|
| vm4         | 1         | x86\_64 | 2GB    | 2GB  |
| vm5         | 2         | x86\_64 | 4GB    | 4GB  |
| pc5         | 4         | x86\_64 | 32GB   | 8GB  |



### 2. Setup Docker Swarm configuration.


```bash
$ ssh pc5
$ docker swarm init
docker swarm join --token {JOIN_TOKEN} {IP ADDRESS}
```

On one of the devices, run the following command to initialize a Docker Swarm and the manager node. For the purposes of the example, pc5 is used.


### 3. Save any arbitrary deep neural network model on the manager node device.

```python

import keras.applications as apps
from keras.models import save_model

save_model(apps.VGG16(), filepath=f"vgg16_model")
```

### 4. Slice the models into layers with the papdl slice command.

```bash
papdl slice vgg16_model -o sliced_vgg16_model
```

### 5. Compile layer performance statistics and inter-device network communications statistics with the papdl benchmark command.

```bash
papdl benchmark sliced_vgg16_model -o benchmarked_vgg16_model
```

### 6. Determine the node ID of the source device from which input data will be provided from


```bash
$ docker node ls
 
VM4 {VM4_NODE_ID}
VM5 {VM5_NODE_ID}
PC5 {PC5_NODE_ID}

```

For this guide, all inputs will be provided from vm4 which has the strongest memory and compute constraints.

### 7. Generate optimal deployment configuration based on aggregated data.

```bash
papdl configure benchmarked_vgg16_model {VM4_NODE_ID} 150528 -o configured_vgg16_model
```

The configure step takes two additional arguments {SOURCE_DEVICE} and {INPUT_SIZE}. {SOURCE_DEVICE} indicates where the source of inputs to perform predictions are coming from.  The {INPUT_SIZE} can be calculated multiplying the input shape of VGG16 which is `224 * 224 * 3 * {batch_size}`. The batch size for this guide will be `1` resulting in an input shape of `224 * 224 * 3 * 1 = 150528`.


### 8. Deploy the model.

```bash
papdl deploy configured_vgg16_model
```

Based on the optimal deployment configuration, we can now containerize sets of layers and distribute them across the configured Docker swarm as micro services. We can verify the instantiation of the services from the following command:

```bash
$ docker service ls
```

### 9. Activate a chain of connections between all the containerized micro services:

```bash
$ ssh vm4
$ curl localhost:8765/connect
$ curl localhost:8765/activate
```

### 10. Perform prediction!

Now we are ready to perform prediction! The `get_papdl_prediction` method shows how we make predictions with PAPDL and `get_local_prediction` method shows how we traditionally make predictions on input using a monolithic DNN architecture running on a single device.

```python
"""
LOCAL MONOLITHIC PREDICTION
"""
def get_local_prediction(image):
    output = model.predict(input)
    prede = vgg16.decode_predictions(output, top=1)
    return pred

"""
DISTRIBUTED PREDICTION WITH PAPDL
"""

def get_papdl_prediction(input):
    buff = io.BytesIO()
    np.save(buff,input)
    buff.seek(0)

    response = requests.post("http://localhost:8765/input",data=buff.read(), verify=False, stream=True)

    result_buff = io.BytesIO()
    result_buff.write(response.content)
    result_buff.seek(0)
    result_np = np.load(result_buff)

    pred = vgg16.decode_predictions(result_np,top=1)
    return pred



def predict(dataset):
    fix,ax = plt.subplots(nrows=1,ncols=len(dataset),figsize=(20,20))
    for i,(image,sample) in enumerate(dataset):
        # display(image)
        input = sample.reshape((-1,224,224,3))
        pred = get_papdl_prediction(input)

        ax[i].imshow(sample.astype("uint8"),interpolation="nearest")
        ax[i].get_xaxis().set_visible(False)
        ax[i].get_yaxis().set_visible(False)
        ax[i].set_title(f"{pred[0][0][2]} {pred[0][0][1]}")

def load_data(images):
    result = []
    for filename in images:
        image = load_img(filename,target_size=(224,224))
        result.append((image, img_to_array(image)))
    return result

predic(dataset)
```

If all goes well, we can verify the output below:

![PAPDL prediction](./scripts/predictions/outputs/papdl.png)


## That easy?

Yes!

