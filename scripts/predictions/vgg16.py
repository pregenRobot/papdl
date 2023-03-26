from keras.datasets import cifar10
from keras.applications import vgg16
from random import randint
import requests
import numpy as np
import io
import sys
import matplotlib.pyplot as plt
    

def benchmark():
    cifar10dataset = cifar10.load_data()
    model = vgg16.VGG16(include_top = False, input_shape=(32,32,3))

    REPEAT = 1
    ASNC = 1
    BATCH_SIZE = 1

    for r in range(REPEAT):
        index = randint(0,49_000)
        random_input = cifar10dataset[0][0][index:index+BATCH_SIZE]
        plt.imshow(random_input[0],interpolation="nearest")
        # print(vgg16.decode_predictions(model.predict(random_input)))
        
        
if __name__ == "__main__":
    benchmark()
