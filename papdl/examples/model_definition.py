
from ..papdl.loader import Loader
import keras
from keras import layers
import numpy as np

num_classes = 10
input_shape = (1000,100)

model = keras.Sequential([
    keras.Input(shape=input_shape),
    layers.Dense(100,activation="relu"),
    layers.Dense(200,activation="relu"),
    layers.Dense(num_classes,activation="softmax")
])

l = Loader(load_type="object", reference=model)

print(l.sliced_network)
