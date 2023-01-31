from time import time
import numpy as np
from getpass import getuser
from glob import glob
from keras.models import Model, load_model
from typing import Dict,TypedDict,List
from json import dumps
from io import BytesIO
from os import stat,environ
import iperf3
from pythonping import ping
from getpass import getuser

def load_all_models()->Dict[str,Model]:
   model_paths = glob(f"/home/{getuser()}/models/*/")

   models:Dict[str,Model]={}
   for model_path in model_paths:
      model = load_model(model_path)
      model_name = model_path.split("/")[-2]
      print(f"Loaded model: {model_path}")
      models[model_name] = model
   return models

class Config(TypedDict):
   number_of_repeats:int
   batch_size:int

config:Config
def load_benchmark_configs():
   # TODO: read from environment variables
   global config
   config = Config(number_of_repeats=100,batch_size=1)
   
def load_network_benchmark_ips()->List[str]:
   return environ.get("PAPDL_WORKERS").split(" ")

def benchmark_time(model:Model)->float:
   global config
   dimensions = (config["batch_size"],) + model.input_shape[1:]
   sample_input = np.random.random_sample(dimensions)
   
   start = time()
   [model(sample_input) for i in range(config["number_of_repeats"])]
   end = time()
   return (end - start)/config["number_of_repeats"]

def benchmark_size(model:Model)->float:
   global config
   dimensions = (config["batch_size"],) + model.input_shape[1:]
   sample_input = np.random.random_sample(dimensions)
   
   output:np.array = model(sample_input, training=False)
   
   # buffer = BytesIO()
   # np.savez(buffer,x=output)
   np.save("fsize",output)
   size = stat("fsize.npy").st_size
   return size

class BenchmarkModel(TypedDict):
   benchmark_size:float
   benchmark_time:float

class BenchmarkNetwork(TypedDict):
   latency:float
   bandwidth:float
   
def benchmark_model()->Dict[str,BenchmarkModel]:
   print(f"Running as: {getuser()} ")
   global config
   models = load_all_models()
   load_benchmark_configs()
   results:Dict[str,BenchmarkModel] = {}
   for i,(name,model) in enumerate(models.items()):
      time = benchmark_time(model)
      size = benchmark_size(model)
      results[name] = BenchmarkModel(benchmark_time=time,benchmark_size=size)

   return results

def benchmark_network()->Dict:
   # return load_network_benchmark_ips()
   while True:
      continue
   result = {}
   client = iperf3.Client()
   for ip in load_network_benchmark_ips():
      client.duration = 1
      client.server_hostname = ip
      client.port = 5201
      r:iperf3.TestResult = client.run()
      
      result[ip] = {
         "sent_bps": r.sent_bps,
         "recieved_bps":r.received_bps,
      }
      
      print(result[ip])
   return result

benchmark_result = {
   "model_performance":benchmark_model(),
   "network_performance":benchmark_network()
}      
      
print("[BENCHMARK]" + dumps(benchmark_result))
