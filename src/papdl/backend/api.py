import docker
import os
from enum import Enum
import getpass

from docker.models.nodes import Node
from docker.models.services import Service
from docker.models.images import Image
from docker.models.containers import Container
from docker.models.networks import Network

from typing import List
from random_word import RandomWords

class Command(Enum):
    SERVER = "server"
    BENCHMARK = "benchmark"

class PapdlAPI:
    def __init__(self, context_name = RandomWords().get_random_word()):
        self.client = docker.from_env()
        self.dircontext = {}
        self.dircontext["api_module_path"] = os.path.dirname(os.path.abspath(__file__))
        self.local_user = getpass.getuser()
        self.local_uid = os.getuid()
        self.context_name = context_name
    
    def build_orchestrator(self) -> str:
        print("Building Orchestrator")
        path = os.path.join(self.dircontext["api_module_path"], "Orchestrator")
        name = f"{self.context_name}-orchestrator"
        self.client.images.build(path,
            name=name, 
            buildargs={
            "local_user": self.local_user,
            "local_uid": self.local_uid,
        })
        return name

    def build_slice(self, model_path: str, id:str)->Image:
        print(f"Building Model {id} : {model_path} ")
        path = os.path.join(self.dircontext["api_module_path"], "Slice")
        name = f"{self.context_name}-slice-{id}"
        return self.client.images.build(
            path,
            name,
            buildargs={
            "local_user": self.local_user,
            "local_uid": self.local_uid,
            "model": model_path
        })
    
    def available_devices(self)->List[Node]:
        return self.client.nodes.list()

    def container_built(self,hash:str, tag:str) -> bool:
        for image in self.client.images.list():
            if image.id == hash and image.tags[0] == tag:
                return True
        return False
    
    def spawn(self, image:str, id:str, command:Command,node:str) -> Service:
        print(f"Spawning service {id} from {image} with {command}")
        return self.client.services.create(
            image=image,
            command=f"python3 -m {command.value}",
            name=f"{image}-{id}",
            constraints=[f"node.id=={node}"],
            user=f"{self.local_user}:{self.local_user}",
            log_driver="json-file"
        )