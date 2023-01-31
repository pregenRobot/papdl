from shutil import copytree,copyfile
from typing import List,TypedDict,Generator,Dict
from docker.models.images import Image
from docker.models.services import Service
from .common import Preferences,LoadingBar,AppType
from random_word import  RandomWords
from getpass import getuser
from os import getuid,path
from tempfile import mkdtemp

import docker

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

class PapdlAPIContext:
    def __init__(self,preference:Preferences, project_name = None, certSubject:CertSpecs=None):
        project_name:str
        r = RandomWords()
        if project_name == None:
            # MACOS
            # project_name = open("/usr/share/dict/words").readlines()[floor(random()*235886)][:-1]
            project_name = r.get_random_word()
        
        self.logger = preference["logger"]
        self.client = docker.from_env()
        self.dircontext = {}
        self.local_user = getuser()
        self.local_uid = getuid()
        self.project_name = project_name
        self.loadingBar = LoadingBar()
        self.dircontext["api_module_path"] = path.dirname(path.abspath(__file__))
        self.cleanup_target = CleanupTarget(tempfolders=[],images=[],services=[])
        self.network = self.client.networks.create(
            name=f"{project_name}_overlay",
            driver="overlay",
            labels={
                "papdl":"true",
                "project_name":self.project_name
            }
        )
        self.preference = preference
        
        self.devices = self.client.nodes.list()
        
        if(certSubject == None):
            self.cert_specs = CertSpecs(
                C="UK",
                ST="Fife",
                L="St. Andrews",
                O="University of St Andrews",
                OU="School of Computer Science",
                CN=getuser(),
                emailAddress=f"{getuser()}@st-andrews.ac.uk",
                validity_seconds=10*365*24*60*60
            )

def prepare_build_context(context:PapdlAPIContext)->str:
    build_context = mkdtemp()
    context.cleanup_target["tempfolders"].append(build_context)
    return build_context

def copy_app(context:PapdlAPIContext,app_type:AppType,build_context:str)->str:
    copytree(
        path.join(context.dircontext["api_module_path"],"containers",app_type.value ,"app"),
        path.join(build_context,"app")
    )
    copyfile(
        path.join(context.dircontext["api_module_path"],"containers",app_type.value, "Dockerfile"),
        path.join(build_context,"Dockerfile")
    )
    copyfile(
        path.join(context.dircontext["api_module_path"],"containers",app_type.value, "requirements.txt"),
        path.join(build_context,"requirements.txt")
    )

def get_papdl_service(context:PapdlAPIContext,labels:Dict[str,str]={},name=None):
    query = {}
    if name is not None:
        query["name"] = name
    if(len(labels.keys()) != 0):
        query["label"] = []
        for k,v in labels.items():
            query["label"].append(f"{k}={v}")
    return context.client.services.list(filters=query)

def get_service_status(service:Service)->List[str]:
    return list(map(lambda s: s['Status']['State'], service.tasks()))
    

def print_docker_logs(context:PapdlAPIContext,log_generator:Generator[Dict,None,None]):
    for chunk in log_generator:
        if 'stream' in chunk:
            for line in chunk["stream"].splitlines():
                context.logger.debug(line)