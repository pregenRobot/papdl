import pickle
import tensorflow
import os
from typing import *
import keras
from keras.engine import functional
from keras import models,layers

class Loader:

    def __init__(self, load_type:Literal["sample","path", "object"], reference:Union[str,functional.Functional]):

        self.reference:functional.Functional = None

        if load_type == "sample":
            dirname = os.path.dirname(__file__)
            path = os.path.join(dirname, f"Models/{self.reference}")
            self.model = keras.models.load_model(path)
        elif load_type == "path":
            self.model = keras.models.load_model(self.reference)
        elif load_type == "object":
            self.model = reference

    # Recursively gets the output of a layer, used to build up a submodel
    def get_output_of_layer(layer, new_input, starting_layer_name):
        global layer_outputs
        if layer.name in layer_outputs:
            return layer_outputs[layer.name]

        if layer.name == starting_layer_name:
            out = layer(new_input)
            layer_outputs[layer.name] = out
            return out

        prev_layers = []
        for node in layer._inbound_nodes:
            if isinstance(node.inbound_layers, Iterable):
                prev_layers.extend(node.inbound_layers)
            else:
                prev_layers.append(node.inbound_layers)

        pl_outs = []
        for pl in prev_layers:
            pl_outs.extend([get_output_of_layer(pl, new_input, starting_layer_name)])

        out = layer(pl_outs[0] if len(pl_outs) == 1 else pl_outs)
        layer_outputs[layer.name] = out
        return out

    # Returns a submodel for a specified input and output layer
    def get_model(self, input_layer: int, output_layer: int):
        layer_number = input_layer
        starting_layer_name = self.model.layers[layer_number].name

        if input_layer == 0:
            new_input = self.model.input

            return models.Model(new_input, self.model.layers[output_layer].output)
        else:
            new_input = layers.Input(batch_shape=self.model.get_layer(starting_layer_name).get_input_shape_at(0))

        new_output = get_output_of_layer(selected_model.layers[output_layer], new_input, starting_layer_name)
        model = models.Model(new_input, new_output)

        return model

    # Navigates the model structure to find regions without parallel paths, returns valid split locations
    def create_valid_splits(self) -> List[int]:

        layer_index = 1
        multi_output_count = 0

        valid_splits = []
        for layer in self.model.layers[1:]:

            if len(layer._outbound_nodes) > 1:
                multi_output_count += len(layer._outbound_nodes) - 1

            if type(layer._inbound_nodes[0].inbound_layers) == list:
                if len(layer._inbound_nodes[0].inbound_layers) > 1:
                    multi_output_count -= (len(layer._inbound_nodes[0].inbound_layers) - 1)
            if multi_output_count == 0:
                valid_splits.append(layer_index)
            layer_index += 1

        return valid_splits


