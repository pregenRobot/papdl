from enum import Enum 
from typing import List,Dict,TypedDict
from ..slice.slice import Slice
from ..backend.api import PapdlAPI, Command
from ..backend.common import SliceBehaviourException,Preferences,SplitStrategy
from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.types import RestartPolicy
from time import sleep,time

preferences:Preferences

def benchmark_slices(slice_list: List[Slice]) -> Dict[str,Dict[str,List[str]]]:
    global preferences
    strategy = preferences['split_strategy']

    if strategy == SplitStrategy.SCISSION:
        return scission_strategy(slice_list)
    else:
        raise NotImplementedError

def get_benchmark_results_from_service(service:Service)->List[float]:
    global preferences
    log_read_start = time()
    while True:
        state = service.tasks()[0]['Status']['State']
        if state == 'complete':
            log_line:bytes
            for log_line in service.logs(stdout=True):
                log_decoded = log_line.decode('utf-8')
                if log_decoded[:11] == '[BENCHMARK]':
                    message = log_decoded[11:]
                    return [float(t) for t in message.split(",")]
        else:
            if time() - log_read_start > preferences['service_idle_detection']:
                raise SliceBehaviourException("Slice timed out while benchmarking...")

def benchmark_slice_image_on_device(api:PapdlAPI, slice_image:Image, device:Node, device_id:int) ->List[float]:
    benchmark_result:List[float]
    service:Service
    global preferences
    try:
        rp = RestartPolicy(condition='any',max_attempts=3)
        service = api.spawn(slice_image,device_id,Command.BENCHMARK,device,rp)
        benchmark_result = get_benchmark_results_from_service(service)
    except SliceBehaviourException as e:
        preferences['logger'].error(e.message)
        exit(1)
    finally:
        service.remove()
    return benchmark_result
    

def scission_strategy(slice_list: List[Slice])->Dict[str,Dict[str,List[str]]]:
    global preferences
    statistics = {}
    try:
        api = PapdlAPI(preference=preferences)
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
        
 
def get_optimal_slices(slice_list: List[Slice], arg_preferences: Preferences):
    global preferences
    preferences = arg_preferences
    benchmark_result = benchmark_slices(slice_list)
    print(benchmark_result)
    ## Perform scission optimisation
    
