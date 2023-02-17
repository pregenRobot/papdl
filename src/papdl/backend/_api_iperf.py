from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.types import RestartPolicy,ServiceMode,EndpointSpec,NetworkAttachmentConfig

from .api_common import PapdlAPIContext,get_papdl_service,get_service_status, get_service_node_ip_mapping
from .common import AppType
from ..slice.slice import Slice
from typing import List,TypedDict,Dict
from os import path,mkdir

class PapdlIperfAPI:
    def __init__(self,context:PapdlAPIContext):
        self.context = context
        self.service:Service = None
        
    def get_iperf_node_ip_mapping(self) -> Dict[str,str]:
        return get_service_node_ip_mapping(self.context,self.service)
    
    def spawn_iperfs(
        self,
    )->Service:
        iperf_services = get_papdl_service(self.context,labels={"type":"iperf"})
        if(len(iperf_services) != 0):
            iperf_services[0].remove()

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
        self.service = service
        return service
