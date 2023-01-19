
from json import loads
from typing import Dict, List, TypedDict
import pandas as pd

benchmark_str = """
{
   "t4ldkn8frk9pslz80ce41q2z6":{
      "model_7":{
         "benchmark_time":0.05306863784790039,
         "benchmark_size":928
      },
      "model_5":{
         "benchmark_time":0.0289609432220459,
         "benchmark_size":1328
      },
      "model":{
         "benchmark_time":0.05616474151611328,
         "benchmark_size":928
      },
      "model_2":{
         "benchmark_time":0.01918482780456543,
         "benchmark_size":1728
      },
      "model_4":{
         "benchmark_time":0.0340578556060791,
         "benchmark_size":1728
      },
      "model_6":{
         "benchmark_time":0.02517557144165039,
         "benchmark_size":1328
      },
      "model_1":{
         "benchmark_time":0.034346580505371094,
         "benchmark_size":1328
      },
      "model_3":{
         "benchmark_time":0.03642749786376953,
         "benchmark_size":2128
      },
      "model_8":{
         "benchmark_time":0.02927207946777344,
         "benchmark_size":528
      },
      "model_9":{
         "benchmark_time":0.042054176330566405,
         "benchmark_size":168
      }
   },
   "asdf786ads7fsadfbjas8":{
      "model_7":{
         "benchmark_time":0.025306863784790039,
         "benchmark_size":928
      },
      "model_5":{
         "benchmark_time":0.01089609432220459,
         "benchmark_size":1328
      },
      "model":{
         "benchmark_time":0.025616474151611328,
         "benchmark_size":928
      },
      "model_2":{
         "benchmark_time":0.005918482780456543,
         "benchmark_size":1728
      },
      "model_4":{
         "benchmark_time":0.01540578556060791,
         "benchmark_size":1728
      },
      "model_6":{
         "benchmark_time":0.010517557144165039,
         "benchmark_size":1328
      },
      "model_1":{
         "benchmark_time":0.0154346580505371094,
         "benchmark_size":1328
      },
      "model_3":{
         "benchmark_time":0.015642749786376953,
         "benchmark_size":2128
      },
      "model_8":{
         "benchmark_time":0.010927207946777344,
         "benchmark_size":528
      },
      "model_9":{
         "benchmark_time":0.0202054176330566405,
         "benchmark_size":168
      }
   },
   "gfhvcbn880ch98hdhhd9":{
      "model_7":{
         "benchmark_time":0.005306863784790039,
         "benchmark_size":928
      },
      "model_5":{
         "benchmark_time":0.00289609432220459,
         "benchmark_size":1328
      },
      "model":{
         "benchmark_time":0.005616474151611328,
         "benchmark_size":928
      },
      "model_2":{
         "benchmark_time":0.001918482780456543,
         "benchmark_size":1728
      },
      "model_4":{
         "benchmark_time":0.00340578556060791,
         "benchmark_size":1728
      },
      "model_6":{
         "benchmark_time":0.002517557144165039,
         "benchmark_size":1328
      },
      "model_1":{
         "benchmark_time":0.0034346580505371094,
         "benchmark_size":1328
      },
      "model_3":{
         "benchmark_time":0.003642749786376953,
         "benchmark_size":2128
      },
      "model_8":{
         "benchmark_time":0.002927207946777344,
         "benchmark_size":528
      },
      "model_9":{
         "benchmark_time":0.0042054176330566405,
         "benchmark_size":168
      }
   }
}
"""
performance_statistics = loads(benchmark_str)
def extract_device_list(statistics:Dict)->List[str]:
    return list(set(statistics.keys()))
def parse_network_statistics(file_name:str)->pd.DataFrame:
    return pd.read_csv(file_name)

devices = extract_device_list(performance_statistics)
orchestrator_device = "t4ldkn8frk9pslz80ce41q2z6"
network_statistics =  parse_network_statistics("network_statistics.csv")
#######################

# print(performance_statistics)
# print(devices)
# print(network_statistics.info())

###########################

def create_compute_path(device_list:List[str], orchestrator_device:str, layer_count: int):
    pass
    
    
     
    

