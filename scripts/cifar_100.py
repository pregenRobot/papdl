from keras.applications.vgg16 import VGG16
from keras.utils.vis_utils import plot_model
from keras.models import save_model
from time import time_ns
import numpy as np

model = VGG16()
model.compile()

save_model(model=model,filepath="./vgg16")

input_shape = model.input_shape[1:]
batch_size = 1
dimensions = (batch_size,) + input_shape
sample = np.random.random_sample(dimensions)

begin = time_ns()
result = model(sample)
end = time_ns()
print(end - begin)

