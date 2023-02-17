from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.types import RestartPolicy,NetworkAttachmentConfig

from .api_common import PapdlAPIContext,prepare_build_context,copy_app,get_docker_logs,get_service_node_ip_mapping
from .common import AppType
from ..slice.slice import Slice
from typing import List,TypedDict
from os import path,mkdir


class PapdlBenchmarkAPI:
    def __init__(self,context:PapdlAPIContext):
        self.context = context
        self.services = []

    def prepare_benchmark_build(self, slices:List[Slice])->str:
        self.context.logger.info(f"Preparing benchmark build...")
        build_context = prepare_build_context(self.context)
        model_paths = path.join(build_context,"models")
        mkdir(model_paths)
        
        slice:Slice
        for slice in slices:
            model = slice.model
            model_path = path.join(model_paths,slice.model.name)
            mkdir(model_path)
            model.save(model_path,overwrite=True)
        
        copy_app(self.context,AppType.BENCHMARKER,build_context)
        return build_context
    
    def get_benchmark_node_ip_mapping(self):
        result = {}
        s:Service
        for s in self.services:
            s_node_ip_mapping = get_service_node_ip_mapping(self.context,s)
            result.update(s_node_ip_mapping)
        
        return result

    def build_benchmark_image(self, slices: List[Slice])->Image:
        
        name = f"localhost:443/{self.context.project_name}/benchmark"
        buildargs={
            "local_user": self.context.local_user,
            "local_uid": str(self.context.local_uid),
        }
        build_context = self.prepare_benchmark_build(slices)
        
        self.context.logger.info(f"Building benchmark with image {name} and self.context {build_context}")
        self.context.loadingBar.start()
        image, build_logs = self.context.client.images.build(
            path=build_context,
            tag=name,
            buildargs=buildargs,
            labels={
                "papdl":"true",
                "project_name":self.context.project_name,
                "type":"benchmark"
            }
        )
        get_docker_logs(self.context,build_logs)
        self.context.cleanup_target["images"].append(image)
        self.context.loadingBar.stop()
        
        self.context.logger.info(f"Pushing image {name}")
        self.context.loadingBar.start()
        self.context.client.images.push(name)
        self.context.loadingBar.stop()
        self.context.benchmark_image = image
        return image

    def spawn_benchmarker_on_node(
        self,
        image:Image,
        node:Node,
        iperf_test_ips:List[str]
    )->Service:
        image_name = image.tags[0]
        self.context.logger.info(f"Spawning service for image {image_name}")
        self.context.loadingBar.start()
        # node_ips = list(map(lambda n: n.attrs["Status"]["Addr"],self.context.devices))
        nac = NetworkAttachmentConfig(self.context.network.name)
        
        service = self.context.client.services.create(
            image=image_name,
            command=f"python3 -m server",
            name=f"{self.context.project_name}_benchmark_{node.id}",
            constraints=[f"node.id=={node.id}"],
            # user=f"{self.context.local_user}:{self.context.local_user",
            # user=self.context.local_user,
            restart_policy = RestartPolicy(condition="none"),
            env=[f"PAPDL_WORKERS={' '.join(iperf_test_ips)}"],
            labels={
                "papdl":"true",
                "project_name":self.context.project_name,
                "type":"benchmark"
            },
            networks=[nac]
        )
        self.context.cleanup_target["services"].append(service)
        self.context.loadingBar.stop()
        self.services.append(service)
        return service
        
    
    
        
    