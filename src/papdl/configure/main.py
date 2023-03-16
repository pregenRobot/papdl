import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import click
from .configure import Configuration,SearchConstraints,Configurer
from ..backend.common import prepare_logger
from ..benchmark.benchmark import BenchmarkResult
from logging import DEBUG
import dill as pickle
import traceback


@click.command()
@click.argument("benchmark_result_path")
@click.argument("source_device")
@click.argument("input_size")
@click.option("-o","--output")
@click.option("-c","--search_constraints",type=str,default="")
def configure(
    benchmark_result_path:str,
    source_device:str,
    input_size:str,
    output:str,
    search_constraints:str
):
    try:
        logger = prepare_logger(DEBUG)
        configurer = Configurer(logger=logger)
        
        benchmark_result:BenchmarkResult = None
        with open(benchmark_result_path,"rb") as f:
            benchmark_result = pickle.load(f)
        
        # sc = SearchConstraints(layer_must_be_in_device={},layer_must_not_be_in_device={})
        sc:SearchConstraints = SearchConstraints.parse_from_str(search_constraints)
        
        configuration:Configuration =  configurer.parse_from_benchmark(
            benchmark_result=benchmark_result["result"],
            source_device=source_device,
            input_size=int(input_size), 
            search_constraints=sc,
            model_list=benchmark_result["slice_list"],
            benchmark_pref=benchmark_result["arg_preferences"])
    
        if output is None:
            output = "configuration.pickle"
        with open(output, "wb") as f:
            pickle.dump(configuration,f,protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(f"Saving sliced model list as '{output}'")
    except Exception as e:
        logger.error(traceback.format_exc())
    
    
    
