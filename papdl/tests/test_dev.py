import os

from weakref import ref
from papdl.loader import Loader
from tensorflow import keras
import keras
from keras import layers



def test_loader():
    num_classes = 10
    input_shape = (28,28,1)

    model = keras.Sequential([
        keras.Input(shape=input_shape),
        layers.Conv2D(32, kernel_size=(3,3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.Conv2D(64, kernel_size=(3,3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.Flatten(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax"),
    ])
    l = Loader(load_type="object", reference=model)

    for i, split_point in enumerate(l.create_valid_splits()):
        
        if i == 0:
            first_point = 0
        else:
            first_point = split_point[i - 1] + 1
            
