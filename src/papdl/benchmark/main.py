from enum import Enum 
from typing import List,Dict
from keras.models import Model
from ..slice.slice import Slice
from ..backend.api import PapdlAPI
from ..backend.api import Command
import tempfile
import shutil

class SplitStrategy(Enum):
    ATOMIC = 1
    SCISSION = 2
    SCISSION_TL = 3

def benchmark_slices(slice_list: List[Slice], strategy:SplitStrategy) -> Dict[str,Dict[str,List[str]]]:

    if strategy == SplitStrategy.SCISSION:
        return scission_strategy(slice_list)

def scission_strategy(slice_list: List[Slice])->Dict[str,Dict[str,List[str]]]:
    api = PapdlAPI()
    devices = api.available_devices()
    statistics = {}
    
    for i, slice in enumerate(slice_list):
        model = slice.model
        model_save_path = tempfile.mkdtemp()
        model.save(model_save_path,overwrite=True)
        slice_image = api.build_slice(model_save_path,i)

        slice_image_name = slice_image.tags[-1].split(":")[0]
        statistics[slice.model.name] = {}
        for device in devices:
            service = api.spawn(slice_image_name,id,Command.BENCHMARK,device.id)
            log = ""
            for log_line in service.logs(stdout=True):
                if log_line == "==FINISH==":
                    break
                else:
                    log = log_line
            service.remove()
            statistics[slice.model.name][device.id] = log.split(",")

        shutil.rmtree(model_save_path)
    
 
def get_optimal_slices(slice_list: List[Slice], strategy: SplitStrategy):
    benchmark_result = benchmark_slices(slice_list,strategy)
    print(benchmark_result)
    ## Perform scission optimisation
    
