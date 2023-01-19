from typing import List,Dict
from docker.models.nodes import Node
from ..slice.slice import Slice
from ..backend.api import PapdlAPI
from ..backend.common import LoadingBar, Preferences

def predict_optimal_slices(statistics:Dict[str,Dict[str,float]]):
    device_list = statistics.keys()
    
    
    # statistics: node_id -> model_name -> benchmark
    
    
    