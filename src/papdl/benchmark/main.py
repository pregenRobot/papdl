from enum import Enum 
from typing import List,Dict,TypedDict
from ..slice.slice import Slice
from ..backend.api import PapdlAPI
from ..backend.common import ContainerBehaviourException,Preferences,SplitStrategy,LoadingBar
from ..backend.api_common import PapdlAPIContext
from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.errors import DockerException, APIError
from docker.types import RestartPolicy
from time import sleep,time
from json import loads

preferences:Preferences
loadingBar:LoadingBar

def benchmark_slices(slice_list:List[Slice])->Dict:
    global preferences
    strategy = preferences['split_strategy']
    if strategy == SplitStrategy.SCISSION:
        return scission_strategy(slice_list)
    else:
        raise NotImplementedError

def scission_strategy(slice_list:List[Slice])->Dict:
    global preferences
    statistics = {}
    api:PapdlAPI = None
    try:
        api = PapdlAPI(context=PapdlAPIContext(preference=preferences))
        deployed_services = api.deploy_benchmarkers(slice_list)
        node:Node
        service:Service
        for node,service in deployed_services:
            statistics[node.id] = api.get_service_logs(service)
    except APIError as e:
        preferences['logger'].error(e.response.text)
    except ContainerBehaviourException as e:
        preferences['logger'].error(e.message)
    except DockerException as e:
        preferences['logger'].error("Docker Exception occured. Have you started the client?")
        preferences['logger'].error(e)
    finally:
        if api is not None:
            api.cleanup()
        loadingBar.stop()

def get_optimal_slices(slice_list: List[Slice], arg_preferences:Preferences):
    global preferences
    global loadingBar
    loadingBar = LoadingBar()
    preferences = arg_preferences
    benchmark_results = benchmark_slices(slice_list)
    print(benchmark_results)
