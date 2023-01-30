from enum import Enum
from typing import TypedDict
from keras.models import Model
import tqdm
import logging
from colorama import Fore,Style
from time import time,sleep
from threading import Thread

class LoadingBar():
    bar = [
        " [=          ]",
        " [ =         ]",
        " [  =        ]",
        " [   =       ]",
        " [    =      ]",
        " [     =     ]",
        " [      =    ]",
        " [       =   ]",
        " [        =  ]",
        " [         = ]",
        " [          =]",
        " [         = ]",
        " [        =  ]",
        " [       =   ]",
        " [      =    ]",
        " [     =     ]",
        " [    =      ]",
        " [   =       ]",
        " [  =        ]",
        " [ =         ]",
        " [=          ]",
    ]
    i = 0
    
    def loop(self):
        while self.animate:
            print(self.bar[self.i%len(self.bar)],end="\r")
            self.i+=1
            sleep(1)
            self.i+=1
    
    def start(self):
        self.animate = True
        self.t = Thread(target=self.loop)
        self.t.start()
    
    def stop(self):
        self.animate = False
        

class ContainerBehaviourException(Exception):
    def __init__(self, message:str):
        self.message = message
        super().__init__(self.message)
    
class AppType(Enum):
    ORCHESTRATOR = "Orchestrator"
    BENCHMARKER = "Benchmarker"
    SLICE = "Slice"

class Slice:
    def __init__(self):
        self.model: Model = None
        self.input_layer = 0
        self.output_layer = 0
        self.second_prediction = 0
        self.output_size = 0 

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
    def __init__(self,level=logging.NOTSET):
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

def prepare_logger(level=logging.NOTSET)->logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(ColourFormatter())
    logger.addHandler(ch)
    return logger

class Preferences(TypedDict):
    service_idle_detection: int
    startup_timeout:int
    split_strategy: SplitStrategy
    logger:logging.Logger