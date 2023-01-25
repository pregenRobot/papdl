from enum import Enum 
from typing import List,Dict,TypedDict
from ..slice.slice import Slice
from ..backend.api import PapdlAPI
from ..backend.common import ContainerBehaviourException,Preferences,SplitStrategy,LoadingBar
from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.errors import DockerException, APIError
from docker.types import RestartPolicy
from time import sleep,time
from json import loads

preferences:Preferences
loadingBar:LoadingBar

def benchmark_slices(slice_list: List[Slice]) -> Dict[str,Dict[str,float]]:
    global preferences
    strategy = preferences['split_strategy']

    if strategy == SplitStrategy.SCISSION:
        return scission_strategy(slice_list)
    else:
        raise NotImplementedError

def read_benchmark_results(service:Service)->Dict[str,float]:
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
                    return loads(message)
        else:
            if time() - log_read_start > preferences['service_idle_detection']:
                raise ContainerBehaviourException("Slice timed out while benchmarking...")

def benchmark_on_device(
    api:PapdlAPI,
    benchmark_image:Image,
    device:Node,
    device_id:int) ->Dict:

    benchmark_result={}
    global preferences
    global loadingBar
    try:
        rp = RestartPolicy(condition='none')
        loadingBar.start()
        service = api.spawn(benchmark_image,device_id,device,rp)
        loadingBar.stop()
        preferences['logger'].info("Waiting for benchmark results from device...")
        loadingBar.start()
        benchmark_result = read_benchmark_results(service)
        loadingBar.stop()
    except ContainerBehaviourException as e:
        preferences['logger'].error(e.message)
        exit(1)
    finally:
        api.cleanup()
        loadingBar.stop()
    return benchmark_result

def scission_strategy(slice_list: List[Slice])->Dict[str,Dict[str,float]]:
    global preferences
    statistics = {}
    api:PapdlAPI
    try:
        api = PapdlAPI(preference=preferences)
        devices = api.available_devices()
        
        benchmark_image = api.build_benchmark(slices=slice_list)
        for i,device in enumerate(devices):
            result = benchmark_on_device(api,benchmark_image,device,i)
            statistics[device.id] = result
    except APIError as e:
        preferences['logger'].error(e.response.text)
    except DockerException as e:
        preferences['logger'].error("Docker Exception occured. Have you startd the client?")
    finally:
        if api is not None:
            api.cleanup()
    return statistics
 
def get_optimal_slices(slice_list: List[Slice], arg_preferences: Preferences):
    global preferences
    global loadingBar
    loadingBar = LoadingBar()
    preferences = arg_preferences
    # benchmark_result = benchmark_slices(slice_list)
    # print(benchmark_result)
    api = PapdlAPI(arg_preferences)
    api.secret_gen()
    ## Perform scission optimisation
    
