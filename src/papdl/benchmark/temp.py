
from json import loads,dumps
from enum import Enum
from typing import Dict, List, TypedDict,Union,Set,Tuple,NamedTuple
from copy import deepcopy
import pandas as pd
from collections import deque

test_input = """
{
   "0jv7aoa9p5ll1zxqca7852pkp":{
      "model_performance":{
         "model_5":{
            "benchmark_time":0.0009600341320037842,
            "benchmark_size":1328
         },
         "model_9":{
            "benchmark_time":0.0007116296291351319,
            "benchmark_size":168
         },
         "model_0":{
            "benchmark_time":0.0012714905738830566,
            "benchmark_size":928
         },
         "model_6":{
            "benchmark_time":0.000756922960281372,
            "benchmark_size":1328
         },
         "model_4":{
            "benchmark_time":0.0009644310474395752,
            "benchmark_size":1728
         },
         "model_3":{
            "benchmark_time":0.0009650299549102783,
            "benchmark_size":2128
         },
         "model_1":{
            "benchmark_time":0.0007647640705108642,
            "benchmark_size":1328
         },
         "model_8":{
            "benchmark_time":0.0007638306617736816,
            "benchmark_size":528
         },
         "model_2":{
            "benchmark_time":0.0009319167137145997,
            "benchmark_size":1728
         },
         "model_7":{
            "benchmark_time":0.0007658138275146484,
            "benchmark_size":928
         }
      },
      "network_performance":{
         "0jv7aoa9p5ll1zxqca7852pkp":{
            "bandwidth":{
               "sent_bps":27967170054.26285,
               "received_bps":26865340762.208767
            },
            "latency":{
               "rtt_min_ms":0.0,
               "rtt_avg_ms":0.0,
               "rtt_max_ms":0.02
            }
         },
         "u4epygnre7zj60jmtz6nfoqh3":{
            "bandwidth":{
               "sent_bps":916772831.8971637,
               "received_bps":856761316.6488367
            },
            "latency":{
               "rtt_min_ms":0.24,
               "rtt_avg_ms":0.35,
               "rtt_max_ms":0.54
            }
         },
         "g70ppy9wwa09w5x5al3rqhkk8":{
            "bandwidth":{
               "sent_bps":930054462.7564534,
               "received_bps":868669113.067231
            },
            "latency":{
               "rtt_min_ms":0.27,
               "rtt_avg_ms":0.47,
               "rtt_max_ms":1.5
            }
         }
      }
   },
   "g70ppy9wwa09w5x5al3rqhkk8":{
      "model_performance":{
         "model_6":{
            "benchmark_time":0.0008424403667449951,
            "benchmark_size":1328
         },
         "model_9":{
            "benchmark_time":0.0009128034114837646,
            "benchmark_size":168
         },
         "model_5":{
            "benchmark_time":0.0014638190269470215,
            "benchmark_size":1328
         },
         "model_3":{
            "benchmark_time":0.00109647536277771,
            "benchmark_size":2128
         },
         "model_1":{
            "benchmark_time":0.0008775646686553955,
            "benchmark_size":1328
         },
         "model_7":{
            "benchmark_time":0.0008452577590942383,
            "benchmark_size":928
         },
         "model_4":{
            "benchmark_time":0.0008671987056732178,
            "benchmark_size":1728
         },
         "model_8":{
            "benchmark_time":0.0008331222534179687,
            "benchmark_size":528
         },
         "model_0":{
            "benchmark_time":0.0012930092811584473,
            "benchmark_size":928
         },
         "model_2":{
            "benchmark_time":0.0008685297966003418,
            "benchmark_size":1728
         }
      },
      "network_performance":{
         "0jv7aoa9p5ll1zxqca7852pkp":{
            "bandwidth":{
               "sent_bps":882522.8637524123,
               "received_bps":53595.046866913304
            },
            "latency":{
               "rtt_min_ms":0.28,
               "rtt_avg_ms":0.62,
               "rtt_max_ms":1.92
            }
         },
         "u4epygnre7zj60jmtz6nfoqh3":{
            "bandwidth":{
               "sent_bps":906944414.0616016,
               "received_bps":851076057.6263435
            },
            "latency":{
               "rtt_min_ms":0.31,
               "rtt_avg_ms":0.41,
               "rtt_max_ms":1.43
            }
         },
         "g70ppy9wwa09w5x5al3rqhkk8":{
            "bandwidth":{
               "sent_bps":11752377110.892979,
               "received_bps":11277505010.402567
            },
            "latency":{
               "rtt_min_ms":0.0,
               "rtt_avg_ms":0.0,
               "rtt_max_ms":0.02
            }
         }
      }
   },
   "u4epygnre7zj60jmtz6nfoqh3":{
      "model_performance":{
         "model_8":{
            "benchmark_time":0.0005680563449859619,
            "benchmark_size":528
         },
         "model_1":{
            "benchmark_time":0.0005618522167205811,
            "benchmark_size":1328
         },
         "model_4":{
            "benchmark_time":0.0005836150646209717,
            "benchmark_size":1728
         },
         "model_0":{
            "benchmark_time":0.0008509521484375,
            "benchmark_size":928
         },
         "model_3":{
            "benchmark_time":0.0005839769840240478,
            "benchmark_size":2128
         },
         "model_7":{
            "benchmark_time":0.0005602047443389892,
            "benchmark_size":928
         },
         "model_2":{
            "benchmark_time":0.0005665426254272461,
            "benchmark_size":1728
         },
         "model_9":{
            "benchmark_time":0.0005675253868103027,
            "benchmark_size":168
         },
         "model_5":{
            "benchmark_time":0.0005712642669677734,
            "benchmark_size":1328
         },
         "model_6":{
            "benchmark_time":0.0005655736923217774,
            "benchmark_size":1328
         }
      },
      "network_performance":{
         "0jv7aoa9p5ll1zxqca7852pkp":{
            "bandwidth":{
               "sent_bps":882469.9762686674,
               "received_bps":55801.47766144708
            },
            "latency":{
               "rtt_min_ms":0.19,
               "rtt_avg_ms":0.29,
               "rtt_max_ms":0.67
            }
         },
         "u4epygnre7zj60jmtz6nfoqh3":{
            "bandwidth":{
               "sent_bps":33234176155.877346,
               "received_bps":33233245784.088963
            },
            "latency":{
               "rtt_min_ms":0.0,
               "rtt_avg_ms":0.0,
               "rtt_max_ms":0.02
            }
         },
         "g70ppy9wwa09w5x5al3rqhkk8":{
            "bandwidth":{
               "sent_bps":917023975.5235491,
               "received_bps":891952506.9651792
            },
            "latency":{
               "rtt_min_ms":0.23,
               "rtt_avg_ms":0.43,
               "rtt_max_ms":1.54
            }
         }
      }
   }
}"""

test = loads(test_input)
class Model():
   def __init__(self, name):
      self.name = name

   def __hash__(self):
      return hash(self.name)

   def __eq__(self,other):
      if isinstance(other, Device):
         return other.name == self.name
      else:
         return False
   
   def __str__(self):
      return self.name

class Device():
   def __init__(self, name):
      self.name = name
   
   def __hash__(self):
      return hash(self.name)

   def __eq__(self,other):
      if isinstance(other, Device):
         return other.name == self.name
      else:
         return False
      
   def __str__(self):
      return self.name

devices:List[Device] = [Device(k) for k in list(test.keys())]
source_device = devices[0]

models:List[Model] = [Model(m) for m in sorted(list(test[source_device.name]['model_performance'].keys()))]

input_size = 100
  

class Node():
   def __init__(self,model:Model=None, device:Device=None, paths:List["Path"]=None):
      self.model:Model = model
      self.device:Device = device
      self.paths:List["Path"] = paths
   
   def __hash__(self)->int:
      if self.model is None:
         return hash("NULL" + "-" + self.device.name)
      else:
         return hash(self.model.name + "-" + self.device.name)
   
   def __eq__(self,other:"Node")->bool:
      if isinstance(other,Node):
         if self.model is None and other.model is not None:
            return False

         if other.model is None and self.model is not None:
            return False
         
         if self.model is None and other.model is None:
            return self.device.name == other.device.name

         return self.model.name == other.model.name and self.device.name == other.device.name
      return False
   
   def __str_children(self)->str:
      result = []
      p:"Path"
      for p in self.paths:
         model_name = p['node'].model.name if p['node'].model is not None else "NULL"
         result.append(f"*{model_name}-{p['node'].device.name}-{p['penalty_ms']}*")
      return "\n".join(result)
         
   def __detailstr__(self)->str:
      model_name = "NULL" if self.model is None else self.model.name
      return f"<NODE model:{model_name} device:{self.device.name} children=[\n{self.__str_children()}]>"

   def __str__(self)->str:
      model_name = "NULL" if self.model is None else self.model.name
      return f"<NODE model:{model_name} device:{self.device.name}]>"

class Path(TypedDict):
   node:Node
   penalty_ms:float

visit_node_map:Dict[Node,Node] = {}

def calculate_performance_penalty(destination:Device, model:Model):
   return test[destination.name]["model_performance"][model.name]["benchmark_time"]
def calculate_network_penalty(source:Device, destination:Device, filesize_to_send:int):
   stats = test[source.name]["network_performance"][destination.name]
   latency = stats["latency"]["rtt_avg_ms"] / 1000 # get in seconds
   bandwidth = stats["bandwidth"]["sent_bps"]
   return (latency + (filesize_to_send / bandwidth)) * 1000
def calculate_network_penalty_from_model(source: Device, destination:Device, model:Model):
   filesize_to_send = test[source.name]["model_performance"][model.name]["benchmark_size"]
   return calculate_network_penalty(source,destination,filesize_to_send)
def generate_path(source:Device, destination:Device, next_model:Model)->Path:

   penalty:float
   if next_model is not None:
      ## Generating for first node
      penalty = calculate_network_penalty_from_model(source,destination,next_model)
      penalty += calculate_performance_penalty(destination,next_model)
   else:
      penalty = calculate_network_penalty(source,destination,input_size)
   
   ## If node was previously computed
   temp:Node = Node(model=next_model,device=destination)
   path:Path
   if temp in visit_node_map:
      path = Path(node=visit_node_map.get(temp),penalty_ms=penalty)
   else:
      path = Path(node=Node(model=next_model,device=destination,paths=[]),penalty_ms=penalty)
   return path


def rec_construct_path(models_left:List[Model],currNode:Node):
   ## Check for duplicate node construct here
   if currNode in visit_node_map:
      return

   visit_node_map[currNode] = currNode
   if len(models_left) == 0:
      currNode.paths = [
         generate_path(source=currNode.device,destination=source_device,next_model=None)
      ]
      return
   else:
      paths = [generate_path(currNode.device,d,models_left[0]) for d in devices]
      currNode.paths = paths
      path:Path
      for path in currNode.paths:
         nextNode = path["node"]
         rec_construct_path(models_left=models_left[1:], currNode=nextNode)
         

head = Node(
   model=None,
   device=source_device,
)
## visit_node_map[head] = head
rec_construct_path(models_left=models,currNode=head)

## for n in sorted(visit_node_map.values(),key=lambda n: "n" if n.model is None else n.model.name ):
##    print(n)
##    print("")
import heapq


class SearchStatus(NamedTuple):
   total_distance:float
   path:Path


class SearchCriterion(TypedDict):
   layer_must_be_in_device:Dict[Model,Device]
   layer_must_not_be_in_device:Dict[Model,Device]


def valid_path(path:List[Node],criteria:SearchCriterion):
   for node in path:
      for model,device in criteria["layer_must_be_in_device"].items():
         if model == node.model and device != node.device:
            return False
   
   for node in path:
      for model,device in criteria["layer_must_not_be_in_device"].items():
         if model == node.model and device == node.device:
            return False
   
   return True
   
def find_shortest_loop(start_node:Node,search_criteria:SearchCriterion)->List[Node]:
   visited = {start_node: [start_node]}
   queue:List[SearchStatus] = [SearchStatus(0,Path(node=start_node,penalty_ms=0))]
   while queue:
      total_penalty_ms, path = heapq.heappop(queue)
      current_node = path["node"]
      for child_path in current_node.paths:
         child_node = child_path["node"]
         if child_node not in visited:
            visited[child_node] = visited[current_node] + [child_node] # Make a copy
            new_penalty:float
            if(valid_path(visited[child_node],search_criteria)):
               new_penalty = total_penalty_ms + child_path["penalty_ms"]
            else:
               new_penalty = float('inf')
            heapq.heappush(
               queue,
               SearchStatus(total_distance=new_penalty,path=Path(node=child_node,penalty_ms=new_penalty))
            )
         elif child_node == start_node and len(visited[current_node]) > 1: # Found a loop
            return visited[current_node] + [start_node]
   return [] # No loop found

result = find_shortest_loop(start_node=head,
   search_criteria=SearchCriterion(
      layer_must_be_in_device={},
      layer_must_not_be_in_device={models[0]:source_device}
   )
)


print([n.device.name for n in result])
print(source_device.name)
