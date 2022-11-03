
from papdl.loader import Loader
import socket
from copy import deepcopy
import yaml
import io
from pathlib import Path
import sys
import os
import shutil
from random_word import RandomWords
import keras

r = RandomWords()

class Generator:
    
    def __init__(self,
                 loader:Loader, 
                 test_location:str,
                 test_name:str= r.get_random_word(),
                 forward_url_base:str="0.0.0.0", backward_url_base:str="0.0.0.0"):

        self.loader = Loader
        self.model_structure = {
            "services":{},
            "version": "3.3"
        }
        self.services = []
        self.mapper = {
            "Dense": {
                "build": {"context":"./containers/Dense"},
                "ports": ["8765:LOCAL_FORWARD", "8766:LOCAL_BACKWARD"],
                "environment": [],
                "volumes": ["./Dense/app:/home/app"],
                "entrypoint": "watchmedo auto-restart --pattern \"*.py\" --recursive --signal SIGTERM --directory \"/home/app\" python3 /home/app/server.py"
            },
            "Orchestrator":{
                "build" : {"context": "Orchestrator"},
                "ports" : ["8765:LOCAL_FORWARD", "8766:LOCAL_BACKWARD"],
                "environment": [],
                "volumes": ["./Orchestrator/app:/home/app"],
                "entrypoint": ["watchmedo auto-restart --pattern \"*.py\" --recursive --signal SIGTERM --directory \"/home/app\" python3 /home/app.server.py"]
            }
        }

        self.generate_docker_compose(loader,forward_url_base,backward_url_base)
        self.test_location = test_location
        self.test_name = test_name
        self.create_instance()
        self.configure_instance()
        print(f"Created test: {test_location}/{test_name}")

    # UNSAFE
    def assign_ports(self):
        forward_sock = socket.socket()
        forward_sock.bind(("",0))
        backward_sock = socket.socket()
        backward_sock.bind(("",0))
        self.sockets.append({"forward":forward_sock, "backward":backward_sock})

    
    def map_ports(self,service:dict):
        service["ports"][0] = service["ports"][0].replace(
            "LOCAL_FORWARD",
            str(self.sockets[-1]["forward"].getsockname()[1])
        )
        service["ports"][1] = service["ports"][1].replace(
            "LOCAL_BACKWARD",
            str(self.sockets[-1]["backward"].getsockname()[1])
        )

    def link_containers(self,forward_url_base:str,backward_url_base:str):
        current_service = self.services[-1]["service"]
        prev_service = self.services[-2]["service"]
        
        
        prev_backward_port = self.sockets[-2]["backward"].getsockname()[1]
        curr_forward_port = self.sockets[-1]["forward"].getsockname()[1]

        print(prev_backward_port)
        print("-"*10)
        print(curr_forward_port)

        
        prev_service["environment"].append(f"FORWARD_URL={forward_url_base}")
        prev_service["environment"].append(f"FORWARD_PORT={curr_forward_port}")
        current_service["environment"].append(f"BACKWARD_URL={backward_url_base}")
        current_service["environment"].append(f"BACKWARD_PORT={prev_backward_port}")

        print(prev_service)
        print("-"*10)
        print(current_service)
        print("="*20)
    
    def generate_docker_compose(self,loader:Loader, forward_url_base:str, backward_url_base:str):
        self.sockets = []
        
        orchestrator_service = deepcopy(self.mapper["Orchestrator"])
        orchestrator_name = "orchestrator"
        self.assign_ports()
        self.map_ports(orchestrator_service)
        self.services.append({
            "name": orchestrator_name, 
            "service":orchestrator_service,
            "model": None
        })
        
        for i,f in enumerate(loader.sliced_network):
            layer_type = f.layers[-1].__class__.__name__
            service = deepcopy(self.mapper[layer_type])
            self.assign_ports()
            self.map_ports(service)
            service_name = f"{layer_type}_{i+1}".lower()
            self.services.append({
                "name":service_name,
                "service":service,
                "model":f,
                "layer_type": layer_type
            })
            self.link_containers(forward_url_base,backward_url_base)
        
        self.services[-1]["service"]["environment"].append(f"FORWARD_URL={forward_url_base}")
        self.services[-1]["service"]["environment"].append(f"FORWARD_PORT={self.sockets[0]['forward'].getsockname()[1]}")
        self.services[0]["service"]["environment"].append(f"BACKWARD_URL={backward_url_base}")
        self.services[0]["service"]["environment"].append(f"BACKWARD_PORT={self.sockets[-1]['backward'].getsockname()[1]}")

        for s in self.sockets:
            s["forward"].close()
            s["backward"].close()

        yaml_buff = io.StringIO()
        
        for s in self.services:
            self.model_structure["services"][s["name"]] = s["service"]
    
    def create_instance(self):
        
        if not os.path.exists(self.test_location):
            sys.exit("Test Folder location does not exist")
        self.instance_path = os.path.join(self.test_location,self.test_name)
        os.mkdir(self.instance_path)
        self.volume_folder_path = os.path.join(self.instance_path,"volumes")
        os.mkdir(self.volume_folder_path)
        self.container_path = os.path.join(self.instance_path,"containers")
        os.mkdir(self.container_path)

    def generate_docker_compose_yaml(self):
        yaml_buff = io.StringIO()
        yaml.dump(self.model_structure, yaml_buff)
        yaml_buff.seek(0)
        return yaml_buff.read()

    def configure_instance(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        for s in self.services[1:]:
            model = s["model"]
            service_name = s["name"]
            layer_type = s["layer_type"]
            service_type_path = os.path.join(self.container_path,layer_type)
            if not os.path.exists(service_type_path):
                shutil.copytree(
                    os.path.join(cwd,"containers",layer_type),
                    service_type_path
                )
            
            service_volume_path = os.path.join(self.volume_folder_path,service_name)
            os.mkdir(service_volume_path)
            model_path = os.path.join(service_volume_path,"model")
            model.save(str(model_path))
            model_volume = f"{model_path}:/home/app/model"
            model["service"]["volumes"].append()
        
        with open(os.path.join(self.instance_path,"docker-compose.yml"), "w+") as f:
            f.write(self.generate_docker_compose_yaml())
            