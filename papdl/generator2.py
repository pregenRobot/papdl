from papdl.loader import Loader
from copy import deepcopy
import io,sys,os,shutil
import yaml
from pathlib import Path
from random_word import RandomWords
import keras

r = RandomWords()

class Generator:
    
    def __init__(
        self,
        loader: Loader,
        test_location: str,
        test_name:str = r.get_random_word(),
    ):
        self.loader = loader
        self.test_location = test_location
        self.test_name = test_name

        self.dc_strucutre = {
            "services" : {},
            "version": "3.3",
            "networks":{
                self.test_name: {
                    "driver": "bridge"
                }
            }
        }
        
        self.services = []
        self.templates = {
            "Dense": {
                "build": {"context":"./containers/Dense"},
                "environment": [],
                "volumes": [],
                "networks": [self.test_name],
                "entrypoint": "watchmedo auto-restart --pattern \"*.py\" --recursive --signal SIGTERM --directory \"/home/app\" python3 /home/app/server.py"
            },
            "Orchestrator":{
                "build" : {"context": "./containers/Orchestrator"},
                "environment": [],
                "volumes": [],
                "networks": [self.test_name],
                "entrypoint": "watchmedo auto-restart --pattern \"*.py\" --recursive --signal SIGTERM --directory \"/home/app\" python3 /home/app/server.py"
            }
        }
        
        self.generate_docker_compose()
        self.create_instance()
        self.configure_instance()
        print(f"Created test: {test_location}/{test_name}")
    
    def link_containers(self):
        current_service = self.services[-1]["service"]
        prev_service = self.services[-2]["service"]
        
        prev_service["environment"].append(f"FORWARD_URL={current_service['container_name']}")
        
    
    def generate_docker_compose(self):
        loader:Loader = self.loader
        if loader == None:
            exit("Loader was uninitialized")
        
        orchestrator_service = deepcopy(self.templates["Orchestrator"])
        orchestrator_name = "orchestrator"
        orchestrator_service["container_name"] = orchestrator_name
        self.services.append({
            "service": orchestrator_service,
            "model": None,
            "layer_type": "Orchestrator"
        })
        
        for i,f in enumerate(loader.sliced_network):
            layer_type = f.layers[-1].__class__.__name__
            service = deepcopy(self.templates[layer_type])
            service_name = f"{layer_type}_{i+1}".lower()
            service["container_name"] = service_name
            self.services.append({
                "service": service,
                "model":f,
                "layer_type": layer_type
            })
            self.link_containers()
        
        self.services[-1]["service"]["environment"].append(f"FORWARD_URL={orchestrator_name}")
        
        for s in self.services:
            self.dc_strucutre["services"][s["service"]["container_name"]] = s["service"]
        
        
    def create_instance(self):
        if not os.path.exists(self.test_location):
            sys.exit("Test Folder location does not exist")
        self.instance_path = os.path.join(self.test_location,self.test_name)
        os.mkdir(self.instance_path)
        self.volume_folder_path = os.path.join(self.instance_path, "volumes")
        os.mkdir(self.volume_folder_path)
        self.container_path = os.path.join(self.instance_path,"containers")
        os.mkdir(self.container_path)
    
    def generate_docker_compose_yaml(self):
        yaml_buff = io.StringIO()
        yaml.dump(self.dc_strucutre, yaml_buff)
        yaml_buff.seek(0)
        return yaml_buff.read()

    def copy_container(self,cwd,layer_type):
        service_type_path = os.path.join(self.container_path,layer_type)
        if not os.path.exists(service_type_path):
            shutil.copytree(
                os.path.join(cwd, "containers", layer_type),
                service_type_path
            )
        
    def create_model_volume(self,s):
        model = s["model"]
        service_name = s["service"]["container_name"]
        service_volume_path = os.path.join(self.volume_folder_path,service_name)
        os.mkdir(service_volume_path)
        model_path = os.path.join(service_volume_path,"model")
        model.save(str(model_path))
        model_volume = f"{model_path}:/home/model"
        s["service"]["volumes"].append(model_volume)
    
    def create_app_volume(self,s):
        layer_type = s["layer_type"]
        service_type_path = os.path.join(self.container_path, layer_type)
        app_path = os.path.join(service_type_path,"app")
        app_volume = f"{app_path}:/home/app"
        s["service"]["volumes"].append(app_volume)
    
    def configure_instance(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        for s in self.services[1:]:
            layer_type = s["layer_type"]
            self.copy_container(cwd,layer_type=layer_type)
            self.create_model_volume(s)
            self.create_app_volume(s)
        
        self.copy_container(cwd,"Orchestrator")
        self.create_app_volume(self.services[0])
        
        with open(os.path.join(self.instance_path, "docker-compose.yml"), "w+") as f:
            f.write(self.generate_docker_compose_yaml())
        
        