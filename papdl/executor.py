from papdl.loader import Loader
from tensorflow import keras
import keras
from keras import layers

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

for network in l.sliced_network:
    network.summary()