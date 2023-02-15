from typing import Dict,List,Callable,Optional
from ._api_benchmark import PapdlBenchmarkAPI
from ._api_iperf import PapdlIperfAPI
from ._api_registry import PapdlRegistryAPI
from .api_common import PapdlAPIContext,get_papdl_service,get_service_status
from docker.models.services import Service
from docker.models.nodes import Node
from .common import Slice,ContainerBehaviourException
from time import time,sleep
from ..backend.common import BenchmarkSetup,NodeBenchmarkMetadata,NodeBenchmark,PapdlTest


import json

class PapdlAPI:
    def __init__(self,context:PapdlAPIContext):
        self.context = context
        self.benchmark_api = PapdlBenchmarkAPI(context)
        self.registry_api = PapdlRegistryAPI(context)
        self.iperf_api = PapdlIperfAPI(context)
        
    
    def cleanup(self):
        pass
        
    
    def _all_match_any_of(_all:List[str],_any:List[str])->bool:
        return all([True if x in _any else False for x in _all])
    
    # make timeout on into an enum, turn into sets with all possible states
    def _deploy_service_with_timeout(self,service_spawner:Callable, timeout_on:List[str] ,service_spawner_args={})->Service:
        service = service_spawner(**service_spawner_args)
        self.context.logger.info(f"Spawing service {service.name} ...")
        self.context.loadingBar.start()
        start_time = time()
        while True:
            if time() - start_time > self.context.preference['startup_timeout']:
                raise ContainerBehaviourException(f"Service {service.name} timed out trying to spawn...",service=service)
            else:
                service_status = get_service_status(service)
                self.context.logger.debug(f"Service {service.name} has status: {service_status}")
                if PapdlAPI._all_match_any_of(service_status,timeout_on):
                    break
                if PapdlAPI._all_match_any_of(service_status,["failed", "shutdown", "rejected", "orphaned", "remove"]):
                    raise ContainerBehaviourException(f"Service {service.name} was/has {service_status}",service=service)
                sleep(1)
        self.context.loadingBar.stop()
        return service
    
        
    
    
    def deploy_benchmarkers(self,slices:List[Slice])->Dict[Node,Service]:
        
        registry_service = self._deploy_service_with_timeout(self.registry_api.spawn_registry, ["running","complete"])
        iperf_service = self._deploy_service_with_timeout(self.iperf_api.spawn_iperfs, ["running", "complete"])
        self.context.registry_service = registry_service
        self.context.iperf_service = iperf_service
        
        node_id_ip_mapping = self.iperf_api.get_node_to_iperf_ip_mapping(iperf_service)
        
        self.context.logger.info(f"Node to docker-dns-ip mapping: {node_id_ip_mapping}")
        
        image = self.benchmark_api.build_benchmark_image(slices)
        node:Node
        deployed_services:Dict[Node,Service] = {}
        for node in self.context.devices:
            deployed_services[node] = self._deploy_service_with_timeout(
                self.benchmark_api.spawn_benchmarker_on_node,
                ["complete"],
                {'image':image,'node':node,'iperf_test_ips':node_id_ip_mapping.values()}
            )
        return deployed_services
    
    def get_raw_service_logs(self,service:Service)->str:
        log_read_start = time()
        lines = []
        while True:
            state = service.tasks()[0]['Status']['State']
            if state == 'complete':
                log_line:bytes
                for log_line in service.logs(stdout=True):
                    log_decoded = log_line.decode('utf-8')
                    lines.append(log_decoded)
            else:
                if time() - log_read_start > self.context.preference["service_idle_detection"]:
                    raise ContainerBehaviourException(f"Log reading timed out on service {service.name}",service=Service)
    

    def get_service_logs(self,service:Service)->Dict:
        log_read_start = time()
        while True:
            state = service.tasks()[0]['Status']['State']
            if state == 'complete':
                log_line:bytes
                self.context.logger.debug(f"Retrieved the following logs from the service {service.name}")
                for log_line in service.logs(stdout=True):
                    log_decoded = log_line.decode('utf-8')
                    self.context.logger.debug(log_decoded)
                    if log_decoded[:11] == '[BENCHMARK]':
                        message = log_decoded[11:]
                        return json.loads(message)
            else:
                if time() - log_read_start > self.context.preference['service_idle_detection']:
                    raise ContainerBehaviourException(f"Log reading timed out on service {service.name}",service=service)
                    
                    
            
            
        
        
    
        
        
        