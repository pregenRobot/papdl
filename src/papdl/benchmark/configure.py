from logging import Logger
from typing import NamedTuple,List,Dict,TypedDict,Union,Tuple
from json import loads,dumps
import heapq
from jsonpickle import encode,decode

class Layer():
    def __init__(self,name):
        self.name = name
    
    def __hash__(self):
        return hash(self.name)

    def __eq__(self,other:"Layer"):
        if other is None:
            return False
        if not isinstance(other,Layer):
            return False
        return other.name == self.name

    def __str__(self):
        return self.name

class Worker():
    def __init__(self,name):
        self.name = name
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self,other:"Worker"):
        if other is None:
            return False
        if not isinstance(other,Worker):
            return False
        return other.name == self.name
    
    def __str__(self):
        return self.name

class SearchConstraints(TypedDict):
    layer_must_be_in_device:Dict[Layer,Worker]
    layer_must_not_be_in_device:Dict[Layer,Worker]

class SliceBlock(NamedTuple):
    models:List[Layer]
    slice_index:Tuple[int,int]
    device:Worker

class Configuration(TypedDict):
    models:List[Layer]
    blocks:List[SliceBlock]
    devices:List[Worker]
    constraints:SearchConstraints

class Configurer():
    
    def __init__(self, logger:Logger):
        self.logger = logger

    class DecisionNode():
        def __init__(self,
                     model:Layer=None, 
                     device:Worker=None, 
                     paths:List["Configurer.Path"]=None):
            self.model:Layer = model
            self.device:Worker = device
            self.paths:List[Configurer.Path] = paths
        
        def __hash__(self)->int:
            if self.model is None:
                return hash("NULL" + "-"+self.device.name)
            else:
                return hash(self.model.name+"-"+self.device.name)
        
        def __eq__(self,other:"Configurer.DecisionNode")->bool:
            if other is None:
                return False
            
            if not isinstance(other,Configurer.DecisionNode):
                return False
            
            if(
                self.model is None and other.model is not None or
                self.model is not None and other.model is None
            ):
                return False
            
            if self.model is None and other.model is None:
                return self.device == other.device
            
            return self.model == other.model and self.device == other.device

        def __str_children(self)->str:
            result = []
            p:Configurer.Path
            for p in self.paths:
                model_name = p["node"].model.name if p["node"].model is not None else "NULL"
                result.append(f"*{model_name}-{p['node'].device.name}-{p['penalty_ms']}*")
            return "\n".join(result)
        
        def debug_str(self)->str:
            model_name = "NULL" if self.model is None else self.model.name
            return f"<NODE model:{model_name} device:{self.device.name} children=[\n{self.__str_children()}]>"
        
        def __str__(self)->str:
            model_name = "NULL" if self.model is None else self.model.name
            return f"<NODE model:{model_name} device:{self.device.name}>"

    class Path(TypedDict):
        node:"Configurer.DecisionNode"
        penalty:float


    class OptimalPath(NamedTuple):
        path:List["Configurer.DecisionNode"]
        penalty:float

    class SearchStatus(NamedTuple):
        total_distance:float
        path:"Configurer.Path"

        
    def __valid_path(path:List[DecisionNode],constraints:SearchConstraints):
        node:Configurer.DecisionNode
        for node in path:
            for model,device in constraints["layer_must_be_in_device"].items():
                if model == node.model and device != node.device:
                    return False
        
        for node in path:
            for model,device in constraints["layer_must_not_be_in_device"].items():
                if model == node.model and device == node.device:
                    return False
    
    def __find_shortest_loop(start_node:DecisionNode, constraints:SearchConstraints)-> Union[OptimalPath,None]:
        visited = {start_node:[start_node]}
        queue:List[Configurer.SearchStatus] = [
            Configurer.SearchStatus(total_distance=0,
                path=Configurer.Path(
                    node = start_node,
                    penalty=0
                ))
        ]
        while queue:
            total_penalty,path = heapq.heappop(queue)
            current_node = path["node"]
            for child_path in current_node.paths:
                child_node = child_path["node"]
                if child_node not in visited:
                    new_path = visited[current_node] + [child_node]
                    if Configurer.__valid_path(path=new_path,constraints=constraints):
                        visited[child_node] = new_path
                        new_penalty = total_penalty + child_path["penalty"]
                        
                        heapq.heappush(
                            queue,
                            Configurer.SearchStatus(total_distance=new_penalty,path=Configurer.Path(
                                node=child_node,penalty=new_penalty
                            ))
                        )
                elif child_node == start_node and len(visited[current_node]) > 1:
                    return Configurer.OptimalPath(path=visited[current_node] + [start_node],penalty=child_path["penalty"])
        return None
    
    def __calculate_performance_penalty(
        benchmark_result:Dict,
        destination:Worker,
        model:Layer)->float:
        return benchmark_result[destination.name]["model_performance"][model.name]["benchmark_time"]
    
    def __calculate_network_penalty(
        benchmark_result:Dict,
        source:Worker,
        destination:Worker,
        filesize_to_send:int
    )->float:
        stats = benchmark_result[source.name]["network_performance"][destination.name]
        latency = stats["latency"]["rtt_avg_ms"] / 1000
        bandwidth = stats["bandwidth"]["sent_bps"]
        return (latency + (filesize_to_send/bandwidth))

    def __calculate_network_penalty_from_model(
        benchmark_result:Dict,
        source:Worker,
        destination:Worker,
        model:Layer
    )->float:
        filesize_to_send = benchmark_result[source.name]["model_performance"][model.name]["benchmark_size"]
        return Configurer.__calculate_network_penalty(
            benchmark_result=benchmark_result,
            source=source,
            destination=destination,
            filesize_to_send=filesize_to_send
        )
    
    def __generate_path(
        benchmark_result:Dict,
        source:Worker,
        destination:Worker,
        next_model:Layer,
        input_size:int
    )->Path:
        global visited_node_map

        penalty:float = 0
        if next_model is not None:
            penalty = Configurer.__calculate_network_penalty_from_model(
                benchmark_result=benchmark_result,
                source=source,
                destination=destination,
                model=next_model
            )
            penalty+= Configurer.__calculate_performance_penalty(
                benchmark_result=benchmark_result,
                destination=destination,
                model=next_model
            )
        else:
            penalty += Configurer.__calculate_network_penalty(
                benchmark_result=benchmark_result,
                source=source,
                destination=destination,
                filesize_to_send=input_size
            )

        temp:Configurer.DecisionNode = Configurer.DecisionNode(model=next_model,device=destination)
        path:Configurer.Path
        if temp in visited_node_map:
            path = Configurer.Path(
                node=visited_node_map.get(temp),
                penalty=penalty
            )
        else:
            path = Configurer.Path(
                node=Configurer.node(
                    model=next_model,
                    device=destination,
                    paths=[]
                ),
                penalty=penalty
            )
        return path
    
    def __rec_construct_path(
        benchmark_result:Dict,
        models_left:List[Layer],
        currNode:DecisionNode,
        source_device:Worker,
        devices:List[Worker],
        input_size:int):

        global visited_node_map

        if currNode in visited_node_map:
            return
        
        visited_node_map[currNode] = currNode
        if len(models_left) == 0:
            currNode.paths = [
                Configurer.__generate_path(
                    source=currNode.device,
                    destination=source_device,
                    next_model=None,
                    input_size=input_size
                )
            ]
            return
        else:
            paths = [
                Configurer.__generate_path(
                    benchmark_result=benchmark_result,
                    source=currNode.device,
                    destination=d,
                    next_model=models_left[0],
                    input_size=input_size
                )
                for d in devices
            ]
            currNode.paths = paths
            path:Configurer.Path
            for path in currNode.paths:
                nextNode = path["node"]
                Configurer.__rec_construct_path(
                    benchmark_result=benchmark_result,
                    models_left=models_left[1:],
                    currNode=nextNode,
                    source_device=source_device,
                    devices=devices,
                    input_size=input_size
                )
    
    def __generate_blocks(
        op:OptimalPath
    )->List[SliceBlock]:
        l = 1
        r = 2
        slices:List[SliceBlock] = []
        while r < len(op.path):
            if op.path[r].device != op.path[l].device:
                nodes_slice = op.path[l:r]
                s = SliceBlock(
                    models=[
                        n.model
                        for n in nodes_slice
                    ],
                    slice_index=(l,r),
                    device=op.path[l].device
                )
                l = r
            r+=1
        return slices
    
        
    
    def parse_from_benchmark(
        self,
        benchmark_result:Dict,
        source_device:Union[Worker,str],
        input_size:int,
        search_constraints:SearchConstraints
        )->Configuration:
        devices:List[Worker] = [Worker(k) for k in list(benchmark_result.keys())]
        
        sd:Worker = None
        if isinstance(source_device,Worker):
            sd = source_device
        if isinstance(source_device,str):
            sd = Worker(name=source_device)
        
        models:List[Layer] = [
            Layer(m) for m in sorted(list(
                benchmark_result[sd.name]['model_performance'].keys()
            ))
        ]
        
        global visited_node_map

        ## typing: Dict["Configuration.Node","Configuration.Node"]
        visited_node_map = {}

        head = Configurer.DecisionNode(
            model=None,
            device=sd
        )
        Configurer.__rec_construct_path(
            benchmark_result=benchmark_result,
            models_left=models,
            currNode=head,
            source_device=sd,
            devices=devices,
            input_size=input_size
        )
        shortest_loop = Configurer.__find_shortest_loop(
            start_node=head,
            constraints=search_constraints
        )
        if shortest_loop is None:
            self.logger.error("No path found with the provided constraints")
            exit(1)
        
        blocks = Configurer.__generate_blocks(shortest_loop)
        return Configuration(
            models=models,
            blocks=blocks,
            devices=devices,
            constraints=search_constraints
        )
        
    
    def parse_from_benchmarker_cache(input:str)->Configuration:
        return (Configurer.parse_from_benchmark(loads(input)))
    
    def parse_from_configurer_cache(input:str)->Configuration:
        configuration = decode(input)
        assert(isinstance(configuration,Configuration))
        return configuration
    
    def dump_configuration(configuration:Configuration)->str:
        return encode(configuration)
    
    
    
    