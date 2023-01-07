
import os

from papdl.loader import Loader
from papdl.generator2 import Generator

import keras
from keras import layers
import numpy as np

num_classes = 10
input_shape = (1000,100)

model = keras.Sequential([
    keras.Input(shape=(input_shape[1])),
    layers.Dense(100,activation="relu"),
    layers.Dense(200,activation="relu"),
    layers.Dense(300,activation="relu"),
    layers.Dense(400,activation="relu"),
    layers.Dense(500,activation="relu"),
    layers.Dense(600,activation="relu"),
    layers.Dense(700,activation="relu"),
    layers.Dense(800,activation="relu"),
    layers.Dense(900,activation="relu"),
    layers.Dense(1000,activation="relu"),
    layers.Dense(900,activation="relu"),
    layers.Dense(800,activation="relu"),
    layers.Dense(700,activation="relu"),
    layers.Dense(600,activation="relu"),
    layers.Dense(500,activation="relu"),
    layers.Dense(400,activation="relu"),
    layers.Dense(300,activation="relu"),
    layers.Dense(200,activation="relu"),
    layers.Dense(100,activation="relu"),
    layers.Dense(num_classes,activation="softmax")
])

model.compile(optimizer="Adam", loss="mse",metrics=["mae", "acc"])
test_inputs = np.random.random(input_shape)
test_outputs = np.random.random((input_shape[0],num_classes))
print(test_inputs.shape)
print(test_outputs.shape)
model.fit(test_inputs,test_outputs)

l = Loader(model)
cwd = "/home/maat1/Documents/cs4099/papdl-root/tests"
g = Generator(l,test_location=cwd)