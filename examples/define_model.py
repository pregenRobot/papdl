
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

from papdl.loader import Loader
from papdl.generator import Generator

import keras
from keras import layers

num_classes = 10
input_shape = (1000,100)

model = keras.Sequential([
    keras.Input(shape=input_shape),
    layers.Dense(100,activation="relu"),
    layers.Dense(200,activation="relu"),
    layers.Dense(100,activation="relu"),
    layers.Dense(num_classes,activation="softmax")
])

l = Loader(model)
cwd = "/home/maat1/Documents/cs4099/papdl-root/tests"
g = Generator(l,test_location=cwd)



