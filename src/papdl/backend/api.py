from typing import Dict,List,Callable
from ._api_benchmark import PapdlBenchmarkAPI
from ._api_iperf import PapdlIperfAPI
from ._api_registry import PapdlRegistryAPI
from .api_common import PapdlAPIContext,get_papdl_service,get_service_status
from docker.models.services import Service
from docker.models.nodes import Node
from .common import Slice,ContainerBehaviourException
from time import time


import json

class PapdlAPI:
    def __init__(self,context:PapdlAPIContext):
        self.context = context
        self.benchmark_api = PapdlBenchmarkAPI(context)
        self.registry_api = PapdlRegistryAPI(context)
        self.iperf_api = PapdlIperfAPI(context)
    
    def _deploy_service_with_timeout(self,service_spawner:Callable, service_spawner_args={})->Service:
        service = service_spawner(**service_spawner_args)
        start_time = time()
        while True:
            if time() - start_time > self.context.preference['startup_timeout']:
                raise ContainerBehaviourException(f"Service {service.name} timed out trying to spawn...")
            else:
                service_status = get_service_status(service)
                if service_status in ["running", "complete"]:
                    break
                if service_status in ["failed", "shutdown", "rejected", "orphaned", "remove"]:
                    raise ContainerBehaviourException(f"Service {service.name} was/has {service_status}")
        return service 
    
    def deploy_benchmarkers(self,slices:List[Slice])->Dict[Node,Service]:
        
        registry_service = self._deploy_service_with_timeout(self.registry_api.spawn_registry)
        iperf_service = self._deploy_service_with_timeout(self.iperf_api.spawn_iperfs)
        
        image = self.benchmark_api.build_benchmark_image(slices)
        node:Node
        deployed_services:Dict[Node,Service] = {}
        for node in self.context.devices:
            deployed_services[node] = self._deploy_service_with_timeout(
                self.benchmark_api.spawn_benchmarker_on_node,
                {'image':image,'node':node}
            )
        return deployed_services
    

    def get_service_logs(self,service:Service)->Dict:
        log_read_start = time()
        while True:
            state = service.tasks()[0]['Status']['State']
            if state == 'complete':
                log_line:bytes
                for log_line in service.logs(stdout=True):
                    log_decoded = log_line.decode('utf-8')
                    if log_decoded[:11] == '[BENCHMARK]':
                        message = log_decoded[11:]
                        return json.loads(message)
            else:
                if time() - log_read_start > self.context.preference['service_idle_detection']:
                    raise ContainerBehaviourException(f"Benchmark timed out on service {service.name}")
                    
                    
            
            
        
        
    
        
        
        