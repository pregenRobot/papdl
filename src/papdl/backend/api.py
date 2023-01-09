import docker
import os
import getpass

from docker.models.nodes import Node
from docker.models.services import Service
from docker.models.images import Image
from docker.models.containers import Container
from docker.models.networks import Network
from docker.types import RestartPolicy

from typing import List
from random_word import RandomWords
import tempfile
from .common import Command

from ..slice.slice import Slice
from shutil import copytree,rmtree,copyfile
from .common import Preferences

class PapdlAPI:
    def __init__(self, preference:Preferences, context_name = None):
        context_name:str
        if context_name == None:
            r = RandomWords()
            context_name = r.get_random_word()
        
        self.logger = preference["logger"]
        self.client = docker.from_env()
        self.dircontext = {}
        self.local_user = getpass.getuser()
        self.local_uid = os.getuid()
        self.context_name = context_name

        self.dircontext["api_module_path"] = os.path.dirname(os.path.abspath(__file__))
        self.dircontext["slice_context_path"] = os.path.join(self.dircontext["api_module_path"], "Slice")
        self.dircontext["orchestrator_context_path"] = os.path.join(self.dircontext["api_module_path"], "Orchestrator")

        self.cleanup_target = {
            "tempfolders": [],
            "images": []
        }
    
    def cleanup(self):
        [rmtree(folder) for folder in self.cleanup_target["tempfolders"]]
        # [self.client.images.remove(image.tags[0]) for image in self.cleanup_target["images"]]
        
    def build_orchestrator(self) -> Image:
        self.logger.info("Building orchestrator...")
        path = os.path.join(self.dircontext["api_module_path"], "Orchestrator")
        name = f"{self.context_name}-orchestrator"
        image = self.client.images.build(path,
            name=name, 
            buildargs={
            "local_user": self.local_user,
            "local_uid": self.local_uid,
        })[0]
        self.cleanup_target["images"].append(image)
        return image
    
    
    def prepare_slice_build(self, slice:Slice) -> str:
        self.logger.info(f"Prepareing build for slice {slice.model.name}")
        model = slice.model
        build_context = tempfile.mkdtemp() 
        self.cleanup_target["tempfolders"].append(build_context)

        model_save_path = os.path.join(build_context,"model")
        os.mkdir(model_save_path)
        model.save(model_save_path,overwrite=True)
        
        copytree(
            os.path.join(self.dircontext["slice_context_path"], "app"),
            os.path.join(build_context,"app")
        )
        copyfile(
            os.path.join(self.dircontext["slice_context_path"], "Dockerfile"),
            os.path.join(build_context,"Dockerfile")
        )
        copyfile(
            os.path.join(self.dircontext["slice_context_path"], "requirements.txt"),
            os.path.join(build_context,"requirements.txt")
        )

        return build_context

    # def build_slice(self, model_path: str, id:str)->Image:
    def build_slice(self, slice: Slice, id: str)->Image:
        tag = f"{self.context_name}-slice-{id}"
        buildargs={
            "local_user": self.local_user,
            "local_uid": str(self.local_uid),
        }
        build_context = self.prepare_slice_build(slice)
        self.logger.info(f"Building slice {slice.model.name} with context {build_context}")

        image, build_logs = self.client.images.build(
            path=build_context,
            tag=tag,
            buildargs=buildargs
        )
        
        for chunk in build_logs:
            if 'stream' in chunk:
                for line in chunk['stream'].splitlines():
                    self.logger.debug(line)
        
        self.cleanup_target["images"].append(image)
        return image
    
    def available_devices(self)->List[Node]:
        self.logger.info("Fetching available devices in swarm...")
        return self.client.nodes.list()

    def container_built(self,hash:str, tag:str) -> bool:
        for image in self.client.images.list():
            if image.id == hash and image.tags[0] == tag:
                return True
        return False
    
    def spawn(
        self,
        image:Image,
        id:str,
        command:Command,
        node:Node,
        restart_policy:RestartPolicy
    ) -> Service:
        image_name = image.tags[0].split(":")[0]
        self.logger.info(f"Spawning service for image {image_name}")
        
        service = self.client.services.create(
            image=image_name,
            command=f"python3 -m {command.value}",
            name=f"{image_name}-{id}",
            constraints=[f"node.id=={node.id}"],
            user=f"{self.local_user}:{self.local_user}",
            restart_policy=restart_policy
        )
        return service