from enum import Enum
from typing import TypedDict, Dict, List, Union, NamedTuple, Tuple
import tqdm
import logging
from colorama import Fore, Style
from time import time, sleep
from threading import Thread
from docker.models.services import Service
from docker.models.images import Image
from docker.models.networks import Network
from docker.models.containers import Container
from docker.models.nodes import Node
import coloredlogs




class ContainerBehaviourException(Exception):
    def __init__(self, message: str, service: Service = None):
        self.message = message
        self.service = service
        super().__init__(self.message)


class AppType(Enum):
    ORCHESTRATOR = "Orchestrator"
    BENCHMARKER = "Benchmarker"
    SLICE = "Slice"
    IPERF = "Iperf"
    REGISTRY = "Registry"


class SplitStrategy(Enum):
    ATOMIC = "atomic"
    SCISSION = "scission"
    SCISSION_TL = "scission_tl"

    @staticmethod
    def from_str(label):
        if label == 'scission':
            return SplitStrategy.SCISSION
        elif label == 'scission_tl':
            return SplitStrategy.SCISSION_TL
        elif label == 'atomic':
            return SplitStrategy.ATOMIC
        else:
            raise NotImplementedError


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


class ColourFormatter(logging.Formatter):
    format = "[%(asctime)s - %(levelname)s ] %(message)s (%(filename)s:%(lineno)d)"
    FORMATS = {
        logging.DEBUG: Fore.BLUE + format + Fore.RESET,
        logging.INFO: Fore.YELLOW + format + Fore.RESET,
        logging.ERROR: Fore.RED + format + Fore.RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def prepare_logger(level=logging.DEBUG) -> logging.Logger:
    # logger = logging.getLogger(__name__)
    # logger.setLevel(level)

    # ch = logging.StreamHandler()
    # ch.setLevel(level=level)
    # ch.setFormatter(ColourFormatter())
    # logger.addHandler(ch)
    # logger.propagate = False
    logger = logging.getLogger(__name__)
    logger.propagate = False
    coloredlogs.install(level=level,logger=logger)
    return logger


class PapdlException(Exception):
    def __init__(self,message):
        self.message = message

class BenchmarkPreferences(TypedDict):
    project_name:str

    service_idle_detection: int
    startup_timeout: int
    split_strategy: SplitStrategy
    logger: logging.Logger

    model_test_batch_size:int
    model_test_number_of_repeats:int
    bandwidth_test_duration_sec:int
    latency_test_count:int
    free_memory_multiplier:int



##########


class BenchmarkSetup(TypedDict):
    project_name: str
    registry_service: Service
    iperf_service: Service
    network: Network
    benchmark_image: Image


class NodeBenchmarkMetadata(TypedDict):
    node: Node
    task: Dict
    raw_log: str
    host_ip: str
    docker_dns_ip: str


class NodeBenchmark(TypedDict):
    result: Dict
    metadata: NodeBenchmarkMetadata


class PapdlTest(TypedDict):
    benchmark: List[NodeBenchmark]
    benchmark_setup: BenchmarkSetup
