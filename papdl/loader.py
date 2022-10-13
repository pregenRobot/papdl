import pickle
import tensorflow
import os

class Loader:
    def __init__(self, model_path:str):
        self.model_path = os.path.abspath(model_path)
        self.model = pickle.load(model_path)
