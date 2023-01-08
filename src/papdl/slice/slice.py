from keras.layers import Input
from keras.models import Model
from collections.abc import Iterable
from enum import Enum
from typing import List
        
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
def get_model(input_layer: int, output_layer: int):
    global selected_model

    layer_number = input_layer
    starting_layer_name = selected_model.layers[layer_number].name

    if input_layer == 0:
        new_input = selected_model.input

        return Model(new_input, selected_model.layers[output_layer].output)
    else:
        new_input = Input(batch_shape=selected_model.get_layer(starting_layer_name).get_input_shape_at(0))

    new_output = get_output_of_layer(selected_model.layers[output_layer], new_input, starting_layer_name)
    model = Model(new_input, new_output)

    return model


# Navigates the model structure to find regions without parallel paths, returns valid split locations
def create_valid_splits():
    global selected_model
    model = selected_model

    layer_index = 1
    multi_output_count = 0

    valid_splits = []
    for layer in model.layers[1:]:

        if len(layer._outbound_nodes) > 1:
            multi_output_count += len(layer._outbound_nodes) - 1

        if type(layer._inbound_nodes[0].inbound_layers) == list:
            if len(layer._inbound_nodes[0].inbound_layers) > 1:
                multi_output_count -= (
                        len(layer._inbound_nodes[0].inbound_layers) - 1)

        if multi_output_count == 0:
            valid_splits.append(layer_index)

        layer_index += 1

    return valid_splits 


selected_model = None


class Slice:
    def __init__(self):
        self.model: Model = None
        self.input_layer = 0
        self.output_layer = 0
        self.second_prediction = 0
        self.output_size = 0

def slice_model(model: Model)->List[Slice]:
    global selected_model
    global layer_outputs
    layer_outputs = {}
    selected_model = model

    split_points = create_valid_splits()
    
    sliced_network: List[Slice] = []

    for index, split_point in enumerate(split_points):

        result = Slice()
        result.model = model

        if index == 0:
            first_point = 0
        else:
            first_point = split_points[index - 1] + 1

        result.input_layer = first_point
        result.output_layer = split_point

        result.model = get_model(first_point, split_point)
        sliced_network.append(result)
    
    return sliced_network
