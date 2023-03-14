
from enum import Enum
from typing import List, Dict, TypedDict,Tuple
from ..slice.slice import Slice
from ..backend.api import PapdlAPI, DeploymentStatus
from ..backend.common import ContainerBehaviourException, BenchmarkPreferences, SplitStrategy
from ..backend.api_common import PapdlAPIContext
from docker.models.nodes import Node
from docker.models.services import Service
from docker.errors import DockerException, APIError
from copy import deepcopy

preferences: BenchmarkPreferences


class BenchmarkResult(TypedDict):
    arg_preferences:BenchmarkPreferences
    # papdl_api:PapdlAPI
    result:Dict
    slice_list:List[Slice]

def benchmark_slices(slice_list: List[Slice],arg_preferences: BenchmarkPreferences) -> BenchmarkResult:
    global preferences
    preferences = arg_preferences
    benchmark_results = scission_strategy(slice_list)

    return BenchmarkResult(arg_preferences=arg_preferences,result=benchmark_results,slice_list=[sl.model for sl in slice_list])


def translate_statistics(ds: DeploymentStatus, statistics: Dict) -> Dict:
    ip_to_node_mapping = {v: k for k, v in ds.node_ip_mapping.items()}
    new_statistics = {}
    for device, device_statistics in statistics.items():
        new_statistics[device] = {
            "model_performance": None,
            "network_performance": {},
            "free_memory": deepcopy(device_statistics)["free_memory"]
            }
        new_statistics[device]["model_performance"] = deepcopy(
            device_statistics["model_performance"])
        for ip, network_benchmark in device_statistics["network_performance"].items(
        ):
            new_statistics[device]["network_performance"][ip_to_node_mapping[ip]] = deepcopy(
                network_benchmark)

    return new_statistics


def scission_strategy(slice_list: List[Slice]) -> Dict:
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
    return translate_statistics(ds, statistics)


