import docker
import os,sys
import getpass

from copy import deepcopy

from OpenSSL import crypto, SSL

from docker.models.nodes import Node
from docker.models.services import Service
from docker.models.images import Image
from docker.models.containers import Container
from docker.models.networks import Network
from docker.models.secrets import Secret
from docker.types import RestartPolicy,EndpointSpec,TaskTemplate,SecretReference

from typing import List,Generator,Dict,TypedDict,Tuple
import tempfile

from ..slice.slice import Slice
from shutil import copytree,rmtree,copyfile
from .common import Preferences,AppType,LoadingBar
from random import random,randint
from math import floor
from random_word import RandomWords

import urllib.parse

class CleanupTarget(TypedDict):
    tempfolders:List[str]
    images:List[Image]
    services:List[Service]

class CertSpecs(TypedDict):
    C:str
    ST:str
    L:str
    O:str
    OU:str
    CN:str
    emailAddress:str
    validity_seconds:int
    

class PapdlAPI:
    def __init__(self, preference:Preferences, project_name = None, certSubject:CertSpecs=None):
        project_name:str
        r = RandomWords()
        if project_name == None:
            # MACOS
            # project_name = open("/usr/share/dict/words").readlines()[floor(random()*235886)][:-1]
            project_name = r.get_random_word()
        
        self.logger = preference["logger"]
        self.client = docker.from_env()
        self.dircontext = {}
        self.local_user = getpass.getuser()
        self.local_uid = os.getuid()
        self.project_name = project_name
        self.loadingBar = LoadingBar()
        self.dircontext["api_module_path"] = os.path.dirname(os.path.abspath(__file__))
        self.cleanup_target = CleanupTarget(tempfolders=[],images=[],services=[])
        
        if(certSubject == None):
            self.cert_specs = CertSpecs(
                C="UK",
                ST="Fife",
                L="St. Andrews",
                O="University of St Andrews",
                OU="School of Computer Science",
                CN=getpass.getuser(),
                emailAddress=f"{getpass.getuser()}@st-andrews.ac.uk",
                validity_seconds=10*365*24*60*60
            )
    
    def cert_gen(self,cert_path:os.PathLike, key_path:os.PathLike):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 4096)
        cert = crypto.X509()
        cert.get_subject().C = self.cert_specs["C"]
        cert.get_subject().ST = self.cert_specs["ST"]
        cert.get_subject().L = self.cert_specs["L"]
        cert.get_subject().O = self.cert_specs["O"]
        cert.get_subject().OU = self.cert_specs["OU"]
        cert.get_subject().CN = self.cert_specs["CN"]
        cert.get_subject().emailAddress = self.cert_specs["emailAddress"]
        cert.set_serial_number(randint(1,sys.maxsize - 1))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(self.cert_specs["validity_seconds"])
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k,'sha256')

        with open(cert_path, "wt") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
        
        with open(key_path, "wt") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))
    
    def secret_gen(self):
        cert_path = os.path.join(self.dircontext["api_module_path"],"certificates", "registry.crt")
        key_path = os.path.join(self.dircontext["api_module_path"], "certificates", "registry.key")
        if(not (os.path.isfile(cert_path) and os.path.isfile(key_path))):
            self.cert_gen(cert_path,key_path)
            
        docker_cert_names = list(map(lambda cert: cert.name , self.client.secrets.list()))
        
        
        if('registry.crt' not in docker_cert_names or 'registry.key' not in docker_cert_names):
            cert_data:str = b""
            key_data:str = b""
            
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            
            with open(key_path, "rb") as f:
                key_data = f.read()

            registry_crt = self.client.secrets.create(name="registry.crt",data=cert_data)
            registry_key = self.client.secrets.create(name="registry.key",data=key_data)
            
            return registry_crt,registry_key
        else:
            registry_crt = list(filter(lambda s: s.name=="registry.crt",self.client.secrets.list()))[0]
            registry_key = list(filter(lambda s: s.name=="registry.key", self.client.secrets.list()))[0]
            
            return registry_crt, registry_key
    
    def assign_registry_node(self):
        manager_node = self.client.nodes.list(filters={'role':'manager'})[0]
        manager_node_spec = deepcopy(manager_node.attrs['Spec'])
        manager_node_spec["Labels"]["registry"] = 'true'
        manager_node.update(manager_node_spec)
    
    def cleanup(self):
        # self.logger.debug([folder for folder in self.cleanup_target["tempfolders"]])
        # [rmtree(folder) for folder in self.cleanup_target["tempfolders"]]
        # self.logger.debug([image.attrs for image in self.cleanup_target["images"]])
        # [self.client.images.remove(image.tags[0] for image in self.cleanup_target["images"])]
        # self.logger.debug([service.attrs for service in self.cleanup_target["services"]])
        # [service.remove() for service in self.cleanup_target["services"]]
        # self.cleanup_target = CleanupTarget(tempfolders=[],images=[],services=[])
        pass
        
    def build_orchestrator(self) -> Image:
        self.logger.info("Building orchestrator...")
        path = os.path.join(self.dircontext["api_module_path"], "Orchestrator")
        name = f"{self.project_name}-orchestrator"
        image,build_log = self.client.images.build(path,
            name=name, 
            buildargs={
            "local_user": self.local_user,
            "local_uid": self.local_uid,
        })[0]
        self.cleanup_target["images"].append(image)
        return image
    
    def prepare_build_context(self)->str:
        build_context = tempfile.mkdtemp()
        self.cleanup_target["tempfolders"].append(build_context)
        return build_context
    
    def copy_app(self,app_type:AppType,build_context:str) ->str:
        copytree(
            os.path.join(self.dircontext["api_module_path"], app_type.value ,"app"),
            os.path.join(build_context,"app")
        )
        copyfile(
            os.path.join(self.dircontext["api_module_path"], app_type.value, "Dockerfile"),
            os.path.join(build_context,"Dockerfile")
        )
        copyfile(
            os.path.join(self.dircontext["api_module_path"], app_type.value, "requirements.txt"),
            os.path.join(build_context,"requirements.txt")
        )
        
    def prepare_slice_build(self, slice:Slice) -> str:
        self.logger.info(f"Prepareing build for slice {slice.model.name}...")
        model = slice.model
        build_context = tempfile.mkdtemp() 

        model_save_path = os.path.join(build_context,"model")
        os.mkdir(model_save_path)
        model.save(model_save_path,overwrite=True)
        
        self.copy_app(AppType.SLICE, build_context)
        return build_context

    def prepare_benchmark_build(self,slices:List[Slice]) ->str:
        self.logger.info(f"Preparing benchmark build...")
        build_context = self.prepare_build_context()
        model_paths = os.path.join(build_context,"models")
        os.mkdir(model_paths)
        for slice in slices:
            model = slice.model
            model_path = os.path.join(model_paths,slice.model.name)
            os.mkdir(model_path)
            model.save(model_path,overwrite=True)
        
        self.copy_app(AppType.BENCHMARKER, build_context)
        return build_context

    def build_benchmark(self, slices: List[Slice])->Image:

        name = f"localhost:443/{self.project_name}/benchmark"
        buildargs={
            "local_user": self.local_user,
            "local_uid": str(self.local_uid),
        }
        build_context = self.prepare_benchmark_build(slices)

        self.logger.info(f"Building benchmark with image {name} and context {build_context}")
        self.loadingBar.start()
        image, build_logs = self.client.images.build(
            path=build_context,
            tag=name,
            buildargs=buildargs
        )
        self.print_docker_logs(build_logs)
        self.cleanup_target["images"].append(image)
        self.loadingBar.stop()

        self.logger.info(f"Pushing image {name}")
        self.loadingBar.start()
        self.client.images.push(name)
        self.loadingBar.stop()
        return image
    
    def print_docker_logs(self,log_generator:Generator[Dict,None,None]):
        for chunk in log_generator:
            if 'stream' in chunk:
                for line in chunk["stream"].splitlines():
                    self.logger.debug(line)
    
    # def build_slice(self, model_path: str, id:str)->Image:
    def build_slice(self, slice: Slice, id: str)->Image:
        tag = f"{self.project_name}-slice-{id}"
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
        self.print_docker_logs(build_logs)
        self.cleanup_target["images"].append(image)

        return image
    
    def available_devices(self)->List[Node]:
        self.logger.info("Fetching available devices in swarm...")
        return self.client.nodes.list()

    def spawn_distributer(self)->Service:
        self.logger.info(f"Spawning Registry service...")
        self.loadingBar.start()

        self.client.images.pull("registry",tag="latest")
        self.assign_registry_node()
        crt,key = self.secret_gen()

        registry_volume_path = os.path.join(self.dircontext['api_module_path'], 'registry_volume')
        
        endpoint_spec = EndpointSpec(ports={443:443})

        sr_crt = SecretReference(secret_id=crt.id, secret_name=crt.name)
        sr_key = SecretReference(secret_id=key.id, secret_name=key.name)

        service = self.client.services.create(
            image="registry",
            name="registry",
            constraints=[f"node.labels.registry==true"],
            mounts=[
                f"{registry_volume_path}:/var/lib/registry"
            ],
            env=[
                "REGISTRY_HTTP_ADDR=0.0.0.0:443",
                "REGISTRY_HTTP_TLS_CERTIFICATE=/run/secrets/registry.crt",
                "REGISTRY_HTTP_TLS_KEY=/run/secrets/registry.key"
            ],
            secrets=[sr_crt,sr_key],
            maxreplicas=1,
            endpoint_spec=endpoint_spec
        )
        
        self.cleanup_target["services"].append(service)
        self.loadingBar.stop()
        return service

    def spawn(
        self,
        image:Image,
        node:Node,
        restart_policy:RestartPolicy
    ) -> Service:
        image_name = image.tags[0]
        print(image_name)
        print(image.tags)
        self.logger.info(f"Spawning service for image {image_name}")
        
        self.loadingBar.start()
        service = self.client.services.create(
            image=image_name,
            command=f"python3 -m server",
            name=f"{self.project_name}_benchmark_{id}",
            constraints=[f"node.id=={node.id}"],
            user=f"{self.local_user}:{self.local_user}",
            restart_policy=restart_policy
        )
        
        self.cleanup_target["services"].append(service)
        self.loadingBar.stop()
        return service