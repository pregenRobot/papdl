import click
from .configure import Configuration,SearchConstraints,Configurer
from ..backend.common import prepare_logger
from ..benchmark.benchmark import decode_benchmark_result,BenchmarkResult
from logging import DEBUG

@click.command()
@click.argument("benchmark_result_path")
@click.argument("source_device")
@click.argument("input_size")
@click.option("-o","--output")
@click.option("-c","--search_constraints")
def configure(
    benchmark_result_path:str,
    source_device:str,
    input_size:str,
    output:str,
    search_constraints:str
):
    logger = prepare_logger(DEBUG)
    configurer = Configurer(logger=logger)
    
    benchmark_result:BenchmarkResult = None
    with open(benchmark_result_path,"r") as f:
        benchmark_result = decode_benchmark_result(f.read())
    
    sc = SearchConstraints(layer_must_be_in_device={},layer_must_not_be_in_device={})
    
    configuration:Configuration =  configurer.parse_from_benchmark(
        benchmark_result=benchmark_result["result"],source_device=source_device,
        input_size=int(input_size), 
        search_constraints=sc,
        model_list=benchmark_result["slice_list"])
    
    if output is None:
        output = "configuration.json"
    
    with open(output,"w") as f:
        f.write(Configurer.encode_configuration(configuration))
        
    
    
    
