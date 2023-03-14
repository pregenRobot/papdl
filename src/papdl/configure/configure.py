from logging import Logger
from typing import NamedTuple, List, Dict, TypedDict, Union, Tuple
from json import loads, dumps
import heapq
import keras
from ..backend.common import PapdlException
import logging


class Layer():
    def __init__(self, name,memory_usage):
        self.name = name
        self.memory_usage = memory_usage

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: "Layer"):
        if other is None:
            return False
        if not isinstance(other, Layer):
            return False
        return other.name == self.name

    def __str__(self):
        return self.name


class Worker():
    def __init__(self, name,free_memory):
        self.name = name
        self.free_memory = free_memory

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: "Worker"):
        if other is None:
            return False
        if not isinstance(other, Worker):
            return False
        return other.name == self.name

    def __str__(self):
        return self.name


class SearchConstraints(TypedDict):
    layer_must_be_in_device: Dict[Layer, Worker]
    layer_must_not_be_in_device: Dict[Layer, Worker]


class SliceBlock(NamedTuple):
    layers: List[Layer]
    slice_index: Tuple[int, int]
    device: Worker
    model:keras.models.Model


class Configuration(TypedDict):
    slices: List[Layer]
    blocks: List[SliceBlock]
    devices: List[Worker]
    constraints: SearchConstraints
    source_device:Worker
    input_shape: Tuple[int]
    
class ConfigurationPreferences(TypedDict):
    logger: logging.Logger
    search_constraints:SearchConstraints


class Configurer():

    def __init__(self, logger: Logger):
        self.logger = logger

    class DecisionNode():
        def __init__(self,
                     model: Layer = None,
                     device: Worker = None,
                     paths: List["Configurer.Path"] = []):
            self.model: Layer = model
            self.device: Worker = device
            self.paths: List[Configurer.Path] = paths

        def __hash__(self) -> int:
            if self.model is None:
                return hash("NULL" + "-" + self.device.name)
            else:
                return hash(self.model.name + "-" + self.device.name)

        def __eq__(self, other: "Configurer.DecisionNode") -> bool:
            if other is None:
                return False

            if not isinstance(other, Configurer.DecisionNode):
                return False

            if (
                self.model is None and other.model is not None or
                self.model is not None and other.model is None
            ):
                return False

            if self.model is None and other.model is None:
                return self.device == other.device

            return self.model == other.model and self.device == other.device

        def __str_children(self) -> str:
            result = []
            p: Configurer.Path
            for p in self.paths:
                model_name = p["node"].model.name if p["node"].model is not None else "NULL"
                result.append(
                    f"*{model_name}-{p['node'].device.name}-{p['penalty']}*")
            return "\n".join(result)

        def debug_str(self) -> str:
            model_name = "NULL" if self.model is None else self.model.name
            return f"<NODE model:{model_name} device:{self.device.name} children=[\n{self.__str_children()}]>"

        def __str__(self) -> str:
            model_name = "NULL" if self.model is None else self.model.name
            return f"<NODE model:{model_name} device:{self.device.name}>"

    class Path():
        def __init__(self,node:"Configurer.DecisionNode",penalty:float):
            self.node = node
            self.penalty = penalty
        
        def __eq__ (self, other:"Configurer.Path"):
            return isinstance(other,Configurer.Path) and other.penalty == self.penalty
        
        def __lt__ (self, other:"Configurer.Path"):
            return isinstance(other,Configurer.Path) and other.penalty < self.penalty
    

    class OptimalPath(NamedTuple):
        path: List["Configurer.DecisionNode"]
        penalty: float

    class SearchStatus(NamedTuple):
        total_distance: float
        path: "Configurer.Path"

    def __valid_path(path: List[DecisionNode], constraints: SearchConstraints):
        node: Configurer.DecisionNode
        for node in path:
            for model, device in constraints["layer_must_be_in_device"].items(
            ):
                if model == node.model and device != node.device:
                    return False

        node: Configurer.DecisionNode
        for node in path:
            for model, device in constraints["layer_must_not_be_in_device"].items(
            ):
                if model == node.model and device == node.device:
                    return False
                
        node: Configurer.DecisionNode
        node_memory_usage:Dict[Worker,int] = {}
        for node in path:
            if node.device not in node_memory_usage.keys():
                node_memory_usage[node.device] = 0
            if node.model is None:
                continue
            node_memory_usage[node.device]+=node.model.memory_usage
            
            for worker,nmu in node_memory_usage.items():
                if nmu > worker.free_memory:
                    return False
        return True

    def __find_shortest_loop(
        start_node: DecisionNode,
        constraints: SearchConstraints
    ) -> Union[OptimalPath, None]:
        visited = {start_node: [start_node]}
        # queue: List[Configurer.SearchStatus] = [
        #     Configurer.SearchStatus(
        #         total_distance=0,
        #         path=Configurer.Path(
        #             node=start_node,
        #             penalty=0
        #         ))
        # ]
        queue = [(0,Configurer.Path(node=start_node,penalty=0))]
        while queue:
            total_penalty, path = heapq.heappop(queue)
            current_node = path.node
            for child_path in current_node.paths:
                child_node = child_path.node
                if child_node not in visited:
                    new_path = visited[current_node] + [child_node]
                    if Configurer.__valid_path(
                        path=new_path,
                        constraints=constraints
                    ):
                        visited[child_node] = new_path
                        new_penalty = total_penalty + child_path.penalty
                        # new_search_status = Configurer.SearchStatus(
                        #     total_distance=new_penalty,
                        #     path=Configurer.Path(
                        #         node=child_node,
                        #         penalty=new_penalty
                        #     )
                        # )
                        heapq.heappush(queue,(new_penalty, Configurer.Path(node=child_node,penalty=new_penalty)))
                elif child_node == start_node and len(visited[current_node]) > 1:
                    return Configurer.OptimalPath(
                        path=visited[current_node] + [start_node], penalty=child_path.penalty
                    )
        return None

    def __calculate_performance_penalty(
            benchmark_result: Dict,
            destination: Worker,
            model: Layer) -> float:
        return benchmark_result[destination.name]["model_performance"][model.name]["benchmark_time"]

    def __calculate_network_penalty(
        benchmark_result: Dict,
        source: Worker,
        destination: Worker,
        filesize_to_send: int
    ) -> float:
        stats = benchmark_result[source.name]["network_performance"][destination.name]
        latency = stats["latency"]["rtt_avg_ms"] / 1000
        bandwidth = stats["bandwidth"]["sent_bps"]
        return (latency + (filesize_to_send / bandwidth))

    def __calculate_network_penalty_from_model(
        benchmark_result: Dict,
        source: Worker,
        destination: Worker,
        model: Layer
    ) -> float:
        filesize_to_send = benchmark_result[source.name]["model_performance"][model.name]["benchmark_size"]
        return Configurer.__calculate_network_penalty(
            benchmark_result=benchmark_result,
            source=source,
            destination=destination,
            filesize_to_send=filesize_to_send
        )

    def __generate_path(
        benchmark_result: Dict,
        source: Worker,
        destination: Worker,
        next_model: Layer,
        input_size: int
    ) -> Path:
        global visited_node_map

        penalty: float = 0
        if next_model is not None:
            penalty = Configurer.__calculate_network_penalty_from_model(
                benchmark_result=benchmark_result,
                source=source,
                destination=destination,
                model=next_model
            )
            penalty += Configurer.__calculate_performance_penalty(
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

        temp: Configurer.DecisionNode = Configurer.DecisionNode(
            model=next_model, device=destination)
        path: Configurer.Path
        if temp in visited_node_map:
            path = Configurer.Path(
                node=visited_node_map.get(temp),
                penalty=penalty
            )
        else:
            path = Configurer.Path(
                node=Configurer.DecisionNode(
                    model=next_model,
                    device=destination,
                    paths=[]
                ),
                penalty=penalty
            )
        return path

    def __rec_construct_path(
            benchmark_result: Dict,
            models_left: List[Layer],
            currNode: DecisionNode,
            source_device: Worker,
            devices: List[Worker],
            input_size: int):

        global visited_node_map

        if currNode in visited_node_map:
            return

        visited_node_map[currNode] = currNode
        if len(models_left) == 0:
            currNode.paths = [
                Configurer.__generate_path(
                    benchmark_result=benchmark_result,
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
            path: Configurer.Path
            for path in currNode.paths:
                nextNode = path.node
                Configurer.__rec_construct_path(
                    benchmark_result=benchmark_result,
                    models_left=models_left[1:],
                    currNode=nextNode,
                    source_device=source_device,
                    devices=devices,
                    input_size=input_size
                )

    def __fetch_model_from_nodes(nodes:List[DecisionNode],models:List[keras.models.Model])->List[keras.models.Model]:
        result:List[keras.models.Model] = []
        for n in nodes:
            search = [m for m in models if m.name == n.model.name]
            if len(search) != 1:
                raise PapdlException("Model names in benchmark.json does not match model names for the ones used for benchmarking. Rerun benchmarking process...")
            result.append(search[0])
        return result
    
    def __merge_models(models:List[keras.models.Model])->keras.models.Model:
        result_model = keras.models.Sequential()
        for model in models:
            result_model.add(model)
        result_model.build()
        return result_model
        
        
    def __generate_blocks(
        op: OptimalPath,
        models: List[keras.models.Model]
    ) -> List[SliceBlock]:
        l = 1
        r = 2
        slices: List[SliceBlock] = []
        while r < len(op.path):
            
            if op.path[r].device != op.path[l].device:
                nodes_slice = op.path[l:r]
                s = SliceBlock(
                    layers=[
                        n.model
                        for n in nodes_slice
                    ],
                    slice_index=(l, r),
                    device=op.path[l].device,
                    model=Configurer.__merge_models(
                        Configurer.__fetch_model_from_nodes(nodes_slice,models)
                    )
                )
                slices.append(s)
                l = r
            r += 1

        if len(slices) == 0:
            return [
                SliceBlock(
                    layers=[n.model for n in op.path],
                    slice_index=(0, len(op.path)),
                    device=op.path[0].device,
                    model=Configurer.__merge_models(
                        Configurer.__fetch_model_from_nodes(op.path)
                    )
                )
            ]

        return slices

    def parse_from_benchmark(
        self,
        benchmark_result: Dict,
        source_device: Union[Worker, str],
        input_size: int,
        search_constraints: SearchConstraints,
        model_list:List[keras.models.Model]
    ) -> Configuration:
        devices: List[Worker] = [
            Worker(k,benchmark_result[k]["free_memory"]) for k in list(
                benchmark_result.keys())]

        sd: Worker = None
        if isinstance(source_device, Worker):
            sd = source_device
        if isinstance(source_device, str):
            sd = Worker(name=source_device,free_memory=benchmark_result[source_device]["free_memory"])

        # models: List[Layer] = [
        #     Layer(m) for m in sorted(list(
        #         benchmark_result[sd.name]['model_performance'].keys()
        #     ))
        # ]
        models: List[Layer] = []
        def model_total_ordering(k:str):
            _split = k.split("_")
            if len(_split) == 1:
                return 0
            else:
                return int(_split[1])
        sorted_models = sorted(list(benchmark_result[sd.name]["model_performance"].keys()),key=model_total_ordering)
        for m_key in sorted_models:
            model_dict = benchmark_result[sd.name]["model_performance"][m_key]
            models.append(Layer(name=m_key,memory_usage=model_dict["benchmark_memory_usage"]))

        global visited_node_map

        # typing: Dict["Configuration.Node","Configuration.Node"]
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
            constraints=search_constraints,
            # constraints={
            #     "layer_must_not_be_in_device": {
            #         models[0]: sd,
            #         models[1]: devices[1],
            #         models[4]: sd,
            #         models[-1]: devices[1]
            #     },
            #     "layer_must_be_in_device": {}
            # }
        )
        print(shortest_loop)
        if shortest_loop is None:
            self.logger.error("No path found with the provided constraints")
            exit(1)

        blocks = Configurer.__generate_blocks(shortest_loop,model_list)

        print([b.device.name for b in blocks])
        
        input_shape = blocks[0].model.input_shape[1:]

        return Configuration(
            slices=models,
            blocks=blocks,
            devices=devices,
            constraints=search_constraints,
            source_device=sd,
            input_shape=input_shape
        )