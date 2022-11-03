
from keras.engine import functional as kef
from keras import models,layers
from typing import *

class Loader:
    
    def __init__(self, model:kef.Functional):
        self.model: kef.Functional = model
        self.slice()
        
    def slice(self):
        self.create_valid_splits()
        
        self.sliced_network: List[models.Model] = []
        self.sliced_weights: List = []
        for index, split_point in enumerate(self.split_points):
            
            if index == 0:
                first_point = 0
            else:
                first_point = self.split_points[index - 1] + 1
            
            new_model = self.get_model(first_point, split_point)
            self.sliced_network.append(new_model)
            self.sliced_weights.append(new_model.get_weights())

    def get_model(self, input_layer:int, output_layer:int):
        selected_model = self.model
        
        layer_number = input_layer
        starting_layer_name = selected_model.layers[layer_number].name
        
        if input_layer == 0:
            new_input = selected_model.input
            
            return models.Model(new_input, selected_model.layers[output_layer].output)
        else:
            new_input = layers.Input(batch_shape=selected_model.get_layer(starting_layer_name).get_input_shape_at(0))
        
        self.layer_outputs: Dict[str, layers.Layer] = {}
        new_output = self.get_output_of_layer(selected_model.layers[output_layer], new_input, starting_layer_name)
        model = models.Model(new_input, new_output)
        
        return model
    
    def get_output_of_layer(self, layer: layers.Layer, new_input: layers.Input, starting_layer_name: str) -> layers.Layer:
        
        if layer.name in self.layer_outputs:
            return self.layer_outputs[layer.name]
        
        if layer.name == starting_layer_name:
            out = layer(new_input)
            self.layer_outputs[layer.name] = out
            return out
        
        prev_layers: List[layers.Layer] = []
        for node in layer._inbound_nodes:
            if isinstance(node.inbound_layers, Iterable):
                prev_layers.extend(node.inbound_layers)
            else:
                prev_layers.append(node.inbound_layers)
        
        pl_outs: List[layers.Layer] = []
        for pl in prev_layers:
            pl_outs.extend([self.get_output_of_layer(pl, new_input, starting_layer_name)])
        
        out = layer(pl_outs[0] if len(pl_outs) == 1 else pl_outs)
        self.layer_outputs[layer.name] = out
        return out

    def create_valid_splits(self):
        model = self.model
        
        layer_index = 1
        multi_output_count = 0
        valid_splits = []
        for layer in model.layers[1:]:
            
            if len(layer._outbound_nodes) > 1:
                multi_output_count += len(layer._outbound_nodes) - 1
            
            if type(layer._inbound_nodes[0].inbound_layers) == list:
                if len(layer._inbound_nodes[0].inbound_layers) > 1:
                    multi_output_count -= (len(layer._inbound_nodes[0].inbound_layers) - 1)
            
            if multi_output_count == 0:
                valid_splits.append(layer_index)
            
            layer_index +=1
        
        self.split_points:List[int] = valid_splits
            