
from enum import Enum
from typing import List, Dict, TypedDict,Tuple
from ..slice.slice import Slice
from ..backend.api import PapdlAPI, DeploymentStatus
from ..backend.common import ContainerBehaviourException, BenchmarkPreferences, SplitStrategy, LoadingBar
from ..backend.api_common import PapdlAPIContext
from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.errors import DockerException, APIError
from ..backend.common import BenchmarkSetup, NodeBenchmarkMetadata, NodeBenchmark, PapdlTest
from docker.types import RestartPolicy
from time import sleep, time
from json import loads
from copy import deepcopy
from ..configure.configure import Configuration, Configurer
from jsonpickle import encode,decode

preferences: BenchmarkPreferences
loadingBar: LoadingBar


class BenchmarkResult(TypedDict):
    arg_preferences:BenchmarkPreferences
    papdl_api:PapdlAPI
    result:Dict
    slice_list:List[Slice]
    

def encode_benchmark_result(benchmark_result:BenchmarkResult)->str:
    return encode(benchmark_result)

def decode_benchmark_result(json_str:str)->BenchmarkResult:
    return decode(json_str)

def benchmark_slices(slice_list: List[Slice],arg_preferences: BenchmarkPreferences) -> BenchmarkResult:
    global preferences
    global loadingBar
    loadingBar = LoadingBar()
    preferences = arg_preferences
    api,benchmark_results = scission_strategy(slice_list)
    ## configurer = Configurer(logger=arg_preferences["logger"])

    return BenchmarkResult(arg_preferences=arg_preferences,papdl_api=api,result=benchmark_results,slice_list=[sl.model for sl in slice_list])
    ## config = configurer.parse_from_benchmark(
    ##     benchmark_result=benchmark_results,
    ##     source_device="n7fo72rj7bwdbajkyxypa0ev6",
    ##     input_size=100,
    ##     search_constraints=arg_preferences["search_constraints"]
    ## )
    ## with open("temp.json", "w+") as f:
    ##     f.write(Configurer.dump_configuration(config))

    ## with open("temp.json", "r") as f:
    ##     c = Configurer.parse_from_configurer_cache(f.read())
    ##     print([c.device.name for c in c["blocks"]])

def translate_statistics(ds: DeploymentStatus, statistics: Dict) -> Dict:
    ip_to_node_mapping = {v: k for k, v in ds.node_ip_mapping.items()}
    new_statistics = {}
    for device, device_statistics in statistics.items():
        new_statistics[device] = {
            "model_performance": None,
            "network_performance": {}}
        new_statistics[device]["model_performance"] = deepcopy(
            device_statistics["model_performance"])
        for ip, network_benchmark in device_statistics["network_performance"].items(
        ):
            new_statistics[device]["network_performance"][ip_to_node_mapping[ip]] = deepcopy(
                network_benchmark)

    return new_statistics


def scission_strategy(slice_list: List[Slice]) -> Tuple[PapdlAPI,Dict]:
    global preferences
    statistics = {}
    api: PapdlAPI = None
    ds: DeploymentStatus = None
    try:
        pac = PapdlAPIContext(preference=preferences)
        api = PapdlAPI(context=pac)
        ds = api.deploy_benchmarkers(slice_list)
        deployed_services = ds.node_service_mapping
        node: Node
        service: Service
        for node, service in deployed_services.items():
            statistics[node.id] = api.get_service_logs(service)
    except APIError as e:
        preferences['logger'].error(e.response.text)
    except ContainerBehaviourException as e:
        preferences['logger'].error(e.message)
        preferences['logger'].error("=====SERVICE LOGS=====")
        preferences['logger'].error(api.get_service_logs(e.service))
        exit(1)
    except DockerException as e:
        preferences['logger'].error(
            "Docker Exception occured. Have you started the client?")
        preferences['logger'].error(e)
    finally:
        if api is not None:
            api.cleanup()
        loadingBar.stop()
    return api, translate_statistics(ds, statistics)


