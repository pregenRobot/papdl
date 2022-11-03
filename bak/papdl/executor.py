from papdl.loader import Loader
from tensorflow import keras
import keras
from keras import layers
import numpy as np

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

m = l.sliced_network[-1]

test_input = np.random.random((100,1600))
test_target = np.random.random((100,10))

m.compile(optimizer = "adam", loss="mean_squared_error")
m.fit(test_input, test_target)

m.summary()
m.save("./share/last")