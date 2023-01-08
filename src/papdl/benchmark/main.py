from enum import Enum 
from typing import List,Dict
from ..slice.slice import Slice
from ..backend.api import PapdlAPI
from ..backend.api import Command
from docker.models.nodes import Node
from docker.models.images import Image
from docker.types import RestartPolicy
from time import sleep

class SplitStrategy(Enum):
    ATOMIC = "atomic"
    SCISSION = "scission"
    SCISSION_TL = "scission_tl"
    
    @staticmethod
    def from_str(label):
        if label == 'scission':
            return SplitStrategy.SCISSION
        elif label == 'scission_tl':
            return SplitStrategy.SCISSION_TL
        elif label == 'atomic':
            return SplitStrategy.ATOMIC
        else:
            raise NotImplementedError

def benchmark_slices(slice_list: List[Slice], strategy:SplitStrategy) -> Dict[str,Dict[str,List[str]]]:

    if strategy == SplitStrategy.SCISSION:
        return scission_strategy(slice_list)
    else:
        raise NotImplementedError

def benchmark_slice_image_on_device(api:PapdlAPI, slice_image:Image, device:Node, device_id:int) ->List[float]:
    log = ""
    service = None
    rp = RestartPolicy()
    service = api.spawn(slice_image,device_id,Command.BENCHMARK,device,rp)
    sleep(30)
    for log_line in service.logs(stdout=True):
        log_decoded = log_line.decode('utf-8')
        if "==FINISH==" in log_decoded:
            break
        else:
            log = log_decoded
    # service.remove()
    return [float(e) for e in log.split(",")]
    
    

def scission_strategy(slice_list: List[Slice])->Dict[str,Dict[str,List[str]]]:
    statistics = {}
    try:
        api = PapdlAPI()
        devices = api.available_devices()
        
        for i, slice in enumerate(slice_list):
            slice_image = api.build_slice(slice, i)
            statistics[slice.model.name] = {}
            for j,device in enumerate(devices):
                result = benchmark_slice_image_on_device(api, slice_image,device, j)
                statistics[slice.model.name][device.id] = result
    finally:
        api.cleanup()

    return statistics
        
 
def get_optimal_slices(slice_list: List[Slice], strategy: SplitStrategy):
    benchmark_result = benchmark_slices(slice_list,strategy)
    print(benchmark_result)
    ## Perform scission optimisation
    
