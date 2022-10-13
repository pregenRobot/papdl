import pickle
import tensorflow
import os
from typing import *
from tensorflow import keras

class Loader:

    def __init__(self, load_type:Literal["sample","path"], model_path:str):
        if load_type == "sample":
            self.model_path = model_path
            dirname = os.path.dirname(__file__)
            path = os.path.join(dirname, f"Models/{model_path}")
            self.model = keras.models.load_model(path)
        else:
            self.model_path = os.path.abspath(model_path)
            self.model = kerasmodels.load_model(model_path)
        self.create_valid_splits()

    # Navigates the model structure to find regions without parallel paths, returns valid split locations
    def create_valid_splits(self):

        layer_index = 1
        multi_output_count = 0

        valid_splits = []
        for layer in self.model.layers[1:]:

            if len(layer._outbound_nodes) > 1:
                multi_output_count += len(layer._outbound_nodes) - 1

            if type(layer._inbound_nodes[0].inbound_layers) == list:
                if len(layer._inbound_nodes[0].inbound_layers) > 1:
                    multi_output_count -= (
                            len(layer._inbound_nodes[0].inbound_layers) - 1)

            if multi_output_count == 0:
                valid_splits.append(layer_index)

            layer_index += 1

        self.valid_splits = valid_splits


