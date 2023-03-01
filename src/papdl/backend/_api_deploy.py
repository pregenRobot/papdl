
from .api_common import PapdlAPIContext, prepare_build_context, copy_app, AppType
from ..configure.configure import Configuration, SliceBlock
from os import path,mkdir
from typing import TypedDict,List,Union
from .common import PapdlException

from docker.models.services import Service
from docker.models.nodes import Node


class PapdlService:
    
    def __init__(self,context:PapdlAPIContext, sb:SliceBlock, build_context:str,target_node:Union[str,Node]):
        self.slice_block:SliceBlock = sb
        self.build_context:str = build_context
        self.url:str = None
        self.outwards_url:str = None
        self.service:Service = None
        if isinstance(target_node,str):
            nodes = [d for d in context.devices if d.id == target_node]
            if len(nodes) != 1:
                raise PapdlException("Mismatch between nodes in deployment configuration and currently available nodes in swarm. Please rerun benchmarking and configuration") 
            self.target_node = nodes[0]
        else:
            self.target_node = target_node
    
    def service_spawned(self):
        return self.service != None
            
    
    def assign_service(self,url:str,outward_url:str,service:Service):
        self.service = service
        self.outwards_url = outward_url
        self.url = url

class PapdlDeploymentAPI:
    def __init__(self, context:PapdlAPIContext):
        self.context:PapdlAPIContext = context
        
    def prepare_slice_build(self,configuration:Configuration)->List[PapdlService]:
        papdl_services:List[PapdlService] = []
        for sb in configuration["blocks"]:
            model = sb.model
            device_name = sb.device.name
            slice_index = sb.slice_index
            self.context.logger.info(f"Preparing deployment build for slice {slice_index}")
            build_context = prepare_build_context(self.context)
            model_path = path.join(build_context,"model")
            mkdir(model_path)
            model.save(model_path,overwrite=True)
            copy_app(self.context,AppType.SLICE,build_context)
            papdl_services.append(PapdlService(self.context,sb,build_context,device_name))
        return papdl_services
            
            
            
            
            
            
        
        