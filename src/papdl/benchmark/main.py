from enum import Enum 
from typing import List,Dict,TypedDict
from ..slice.slice import Slice
from ..backend.api import PapdlAPI, DeploymentStatus
from ..backend.common import ContainerBehaviourException,Preferences,SplitStrategy,LoadingBar
from ..backend.api_common import PapdlAPIContext
from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.errors import DockerException, APIError
from ..backend.common import BenchmarkSetup,NodeBenchmarkMetadata,NodeBenchmark,PapdlTest
from docker.types import RestartPolicy
from time import sleep,time
from json import loads
from copy import deepcopy

preferences:Preferences
loadingBar:LoadingBar

def benchmark_slices(slice_list:List[Slice])->Dict:
    global preferences
    strategy = preferences['split_strategy']
    if strategy == SplitStrategy.SCISSION:
        return scission_strategy(slice_list)
    else:
        raise NotImplementedError

# def _prepare_cache(self,context:PapdlAPIContext)->PapdlTest:
#     return PapdlTest(
#         benchmark=[],
#         benchmark_setup=BenchmarkSetup(
#             project_name=context.project_name,
#             registry_service=context.registry_service,
#             iperf_service=context.iperf_service,
#             network=context.network,
#             benchmark_image=context.benchmark_image
#         )
#     )
# 
# def _append_to_cache(self,api:PapdlAPI, papdl_test:PapdlTest,node:Node,service:Service, benchmark_result:Dict)->PapdlTest:
#     papdl_test['benchmark'].append(
#         NodeBenchmark(
#             result=benchmark_result,
#             metadata=NodeBenchmarkMetadata(
#                 node=node,
#                 task=service.tasks()[0],
#                 raw_log=api.get_raw_service_logs(service),
#             )
#         )
#     )


## def translate_node_ip_to_node_id(ds:DeploymentStatus, statistics:Dict)->Dict:
##     for device,s in statistics:
##         for ip,network_benchmark in s["network_performance"]:
##             temp = deepcopy(statistics[device][ip])
##             
##             
##             
    

def scission_strategy(slice_list:List[Slice])->Dict:
    global preferences
    statistics = {}
    api:PapdlAPI = None
    try:
        pac = PapdlAPIContext(preference=preferences)
        api = PapdlAPI(context=pac)
        ds = api.deploy_benchmarkers(slice_list)
        deployed_services = ds.node_service_mapping 
        node:Node
        service:Service
        for node,service in deployed_services.items():
            statistics[node.id] = api.get_service_logs(service)
    except APIError as e:
        preferences['logger'].error(e.response.text)
    except ContainerBehaviourException as e:
        preferences['logger'].error(e.message)
        preferences['logger'].error("=====SERVICE LOGS=====")
        preferences['logger'].error(api.get_service_logs(e.service))
        exit(1)
    except DockerException as e:
        preferences['logger'].error("Docker Exception occured. Have you started the client?")
        preferences['logger'].error(e)
    finally:
        if api is not None:
            api.cleanup()
        loadingBar.stop()
    return statistics

def get_optimal_slices(slice_list: List[Slice], arg_preferences:Preferences):
    global preferences
    global loadingBar
    loadingBar = LoadingBar()
    preferences = arg_preferences
    benchmark_results = benchmark_slices(slice_list)
    print(benchmark_results)
