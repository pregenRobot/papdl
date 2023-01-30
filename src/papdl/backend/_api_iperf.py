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
    
    def spawn_iperfs(
        self,
    )->Service:
        iperf_services = get_papdl_service(self.context,labels={"type":"iperf"})
        if(len(iperf_services) != 0):
            return iperf_services[0]

        self.context.logger.info(f"Spawning iperf3 network inspection service...")
        self.context.loadingBar.start()
        self.client.images.pull("networkstatic/iperf3")
        
        es = EndpointSpec(port={5201:5201})
        nac = NetworkAttachmentConfig(self.context.network.name)
        rp = RestartPolicy(condition="always")
        
        service = self.context.services.create(
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
