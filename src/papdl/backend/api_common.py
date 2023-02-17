from shutil import copytree, copyfile
from typing import List, TypedDict, Generator, Dict, Callable, Union
from docker.models.images import Image
from docker.models.services import Service
from docker.models.secrets import Secret
from docker.models.networks import Network
from .common import Preferences, LoadingBar, AppType
from random_word import RandomWords
from getpass import getuser
from os import getuid, path
from tempfile import mkdtemp

import docker


class CleanupTarget(TypedDict):
    tempfolders: List[str]
    images: List[Image]
    services: List[Service]


class CertSpecs(TypedDict):
    C: str
    ST: str
    L: str
    O: str
    OU: str
    CN: str
    emailAddress: str
    validity_seconds: int


class PapdlAPIContext:
    def __init__(self, preference: Preferences = None,
                 project_name=None, certSubject: CertSpecs = None):
        project_name: str
        self.client = docker.from_env()
        if preference is None:
            self.shell = True  # Shell class only to be used as a docker client to access utility methods
            return
        else:
            self.shell = False

        r = RandomWords()
        if project_name is None:
            project_name = r.get_random_word()

        self.logger = preference["logger"]
        self.dircontext = {}
        self.local_user = getuser()
        self.local_uid = getuid()
        self.project_name = project_name
        self.loadingBar = LoadingBar()
        self.dircontext["api_module_path"] = path.dirname(
            path.abspath(__file__))
        self.cleanup_target = CleanupTarget(
            tempfolders=[], images=[], services=[])

        papdl_networks = get_papdl_network(self)
        if (len(papdl_networks) == 0):
            self.network = self.client.networks.create(
                name=f"papdl_overlay",
                attachable=True,
                driver="overlay",
                labels={
                    "papdl": "true"
                }
            )
        else:
            self.network = papdl_networks[0]

        self.preference = preference

        self.devices = list(
            filter(
                lambda n: n.attrs['Status']['State'] == 'ready',
                self.client.nodes.list()))
        self.logger.info(f"Available nodes: {self.devices}")

        # Dynamically set during runtime
        self.registry_service: Union[Service, None] = None
        self.iperf_service: Union[Service, None] = None
        self.benchmark_image: Union[Image, None] = None

        if (certSubject is None):
            self.cert_specs = CertSpecs(
                C="UK",
                ST="Fife",
                L="St. Andrews",
                O="University of St Andrews",
                OU="School of Computer Science",
                CN=getuser(),
                emailAddress=f"{getuser()}@st-andrews.ac.uk",
                validity_seconds=10 * 365 * 24 * 60 * 60
            )


def prepare_build_context(context: PapdlAPIContext) -> str:
    build_context = mkdtemp()
    context.cleanup_target["tempfolders"].append(build_context)
    return build_context


def copy_app(context: PapdlAPIContext, app_type: AppType,
             build_context: str) -> str:
    copytree(
        path.join(
            context.dircontext["api_module_path"],
            "containers",
            app_type.value,
            "app"),
        path.join(build_context, "app")
    )
    copyfile(
        path.join(
            context.dircontext["api_module_path"],
            "containers",
            app_type.value,
            "Dockerfile"),
        path.join(build_context, "Dockerfile")
    )
    copyfile(
        path.join(
            context.dircontext["api_module_path"],
            "containers",
            app_type.value,
            "requirements.txt"),
        path.join(build_context, "requirements.txt")
    )


def _get_papdl_component(list_handler: Callable,
                         labels: Dict[str, str], name=None) -> List:
    query = {}
    if name is not None:
        query["name"] = name
    query["label"] = ["papdl=true"]
    if (len(labels.keys()) != 0):
        for k, v in labels.items():
            query["label"].append(f"{k}={v}")
    print(query)
    return list_handler(filters=query)


def get_papdl_secret(context: PapdlAPIContext,
                     labels: Dict[str, str] = {}, name=None) -> List[Secret]:
    return _get_papdl_component(context.client.secrets.list, labels, name)


def get_papdl_service(context: PapdlAPIContext,
                      labels: Dict[str, str] = {}, name=None):
    return _get_papdl_component(context.client.services.list, labels, name)


def get_papdl_image(context: PapdlAPIContext,
                    labels: Dict[str, str] = {}, name=None):
    return _get_papdl_component(context.client.images.list, labels, name)


def get_papdl_network(context: PapdlAPIContext,
                      labels: Dict[str, str] = {}, name=None):
    return _get_papdl_component(context.client.networks.list, labels, name)


def get_service_status(service: Service) -> List[str]:
    return list(map(lambda s: s['Status']['State'], service.tasks()))


def get_service_node_ip_mapping(context: PapdlAPIContext, service: Service):
    service_tasks = service.tasks()
    mapping = {}
    for task in service_tasks:
        node_id = task['NodeID']
        task_networks = task["NetworksAttachments"]
        project_network_config = list(
            filter(
                lambda n: n['Network']['Spec']['Name'] == context.network.name,
                task_networks))[0]
        task_ip = project_network_config['Addresses'][0]
        ip = task_ip.split("/")[0]
        mapping[node_id] = ip
    return mapping


def get_docker_logs(context: PapdlAPIContext,
                    log_generator: Generator[Dict, None, None]):
    for chunk in log_generator:
        if 'stream' in chunk:
            for line in chunk["stream"].splitlines():
                context.logger.debug(line)
