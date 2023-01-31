from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.types import RestartPolicy,ServiceMode,EndpointSpec,NetworkAttachmentConfig

from .api_common import PapdlAPIContext,get_papdl_service,get_service_status
from .common import Slice,AppType
from typing import List,TypedDict
from os import path,mkdir

class PapdlIperfAPI:
    def __init__(self,context:PapdlAPIContext):
        self.context = context
    
    def get_node_to_iperf_ip_mapping(self,service:Service):
        iperf_tasks = service.tasks()
        mapping = {}
        for task in iperf_tasks:
            node_id = task['NodeID']
            task_networks = task["NetworksAttachments"]
            project_network_config = list(filter(lambda n: n['Network']['Spec']['Name'] == self.context.network.name , task_networks))[0]
            iperf_ip = project_network_config['Addresses'][0]
            ip = iperf_ip.split("/")[0]
            mapping[node_id] = ip
        return mapping
        
    
    def spawn_iperfs(
        self,
    )->Service:
        iperf_services = get_papdl_service(self.context,labels={"type":"iperf"})
        if(len(iperf_services) != 0):
            return iperf_services[0]

        self.context.logger.info(f"Spawning iperf3 network inspection service...")
        self.context.loadingBar.start()
        self.context.client.images.pull("networkstatic/iperf3")
        
        # es = EndpointSpec(ports={5201:5201})
        es = EndpointSpec(mode="vip",ports={5201:5201})
        nac = NetworkAttachmentConfig(self.context.network.name)
        rp = RestartPolicy(condition="any")
        
        service = self.context.client.services.create(
            image="networkstatic/iperf3",
            name=f"iperf",
            mode=ServiceMode(mode="global"),
            endpoint_spec=es,
            networks=[nac],
            restart_policy=rp,
            args=["-s"],
            labels={
                "papdl":"true",
                "type":"iperf"
            }
        )
        self.context.cleanup_target["services"].append(service)
        self.context.loadingBar.stop()
        return service