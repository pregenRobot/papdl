
from .api_common import PapdlAPIContext, prepare_build_context, copy_app, AppType,get_docker_logs
from ..configure.configure import Configuration, SliceBlock
from os import path,mkdir
from typing import TypedDict,List,Union,Dict
from .common import PapdlException

from docker.models.services import Service
from docker.models.nodes import Node
from docker.models.images import Image
from docker.types import NetworkAttachmentConfig,RestartPolicy,EndpointSpec


class PapdlService:
    def __init__(self,context:PapdlAPIContext,build_context:str,target_node:Union[str,Node], apptype:AppType,name:str):
        self.build_context:str = build_context
        if isinstance(target_node,str):
            nodes = [d for d in context.devices if d.id == target_node]
            if len(nodes) != 1:
                raise PapdlException("Mismatch between nodes in deployment configuration and currently available nodes in swarm. Please rerun benchmarking and configuration") 
            self.target_node:Node = nodes[0]
        else:
            self.target_node:Node = target_node
        self.context:PapdlAPIContext = context
        self.apptype:AppType = apptype
        self.image_name = f"localhost:443/{context.project_name}/{name}"
        self.service_name = f"{context.project_name}_{name}"

        self.url:str = None
        self.outwards_url:str = None
        self.service:Service = None
        self.build()

    def service_spawned(self)->bool:
        return self.service != None
        
    def assign_service(self,url:str,outward_url:str,service:Service):
        self.service = service
        self.outwards_url = outward_url
        self.url = url

    def build(self)->"PapdlService":

        buildargs = {
            "local_user": self.context.local_user,
            "local_uid": str(self.context.local_uid)
        }
        self.context.logger.info(
            f"Building {self.image_name} with context {self.build_context}"
        )
        self.context.loadingBar.start()
        image, build_logs = self.context.client.images.build(
            path=self.build_context,
            tag=self.image_name,
            buildargs=buildargs,
            labels={
                "papdl": "true",
                "project_name": self.context.project_name,
                "type": "slice"
            }
        )
        get_docker_logs(self.context,build_logs)
        self.context.cleanup_target["images"].append(image)
        self.context.loadingBar.stop()
        self.context.logger.info(f"Pushing image {self.image_name} to registry for distribution")
        self.context.loadingBar.start()
        self.context.client.images.push(self.image_name)
        self.context.loadingBar.stop()
        self.image = image
        
    def spawn(self)->"PapdlService":
        image_name = self.image.tags[0]
        self.context.logger.info(f"Spawning service for image {image_name}")
        self.context.loadingBar.start()
        nac = NetworkAttachmentConfig(self.context.network.name)
        es = EndpointSpec(mode="vip")
        
        spawning_configuration = {
            "image":image_name,
            "command":f"python3 -m server",
            "constraints":[f"node.id=={self.target_node.id}"],
            "restart_policy":RestartPolicy(condition="none"),
            "labels":{
                "papdl": "true",
                "project_name": self.context.project_name,
                "type":self.apptype.value
            },
            "name":self.service_name,
            "endpoint_spec":es,
            "networks":[nac]
        }
        self.service = self.context.client.services.create(**spawning_configuration)
        self.context.cleanup_target["services"].append(self.service)
        self.context.loadingBar.stop()
        return self


class PapdlSliceService(PapdlService):
    def __init__(self,context:PapdlAPIContext, sb:SliceBlock):
        slice_indices = sb.slice_index
        slice_start = slice_indices[0]
        slice_end = slice_indices[1]
        name = f"slices_{slice_start}_{slice_end}"

        self.slice_block:SliceBlock = sb
        
        context.logger.info(f"Preparing deployment build for slice {slice_indices}")
        build_context = prepare_build_context(context)
        model_path = path.join(build_context,"model")
        mkdir(model_path)
        model = sb.model
        model.save(model_path,overwrite=True)
        copy_app(context,AppType.SLICE,build_context=build_context)
        target_node = sb.device.name

        super().__init__(context=context,build_context=build_context,target_node=target_node,apptype=AppType.SLICE, name=name)
        
class PapdlOrchestratorService(PapdlService):
    def __init__(self,context:PapdlAPIContext, configuration:Configuration):
        name = f"{context.project_name}_orchestrator"
        context.logger.info(f"Preparing orchestrator build...")
        build_context = prepare_build_context(context)
        copy_app(context=context,app_type=AppType.ORCHESTRATOR,build_context=build_context)
        source_device = configuration["source_device"].name
        super().__init__(context=context,build_context=build_context,target_node=source_device,apptype=AppType.ORCHESTRATOR,name=name)
    
            
            
            
            
            
        
        