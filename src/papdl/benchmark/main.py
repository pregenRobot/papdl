import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import click
from ..backend.common import prepare_logger,BenchmarkPreferences
from ..benchmark.benchmark import benchmark_slices,SplitStrategy,BenchmarkResult
from logging import DEBUG
import traceback
import dill as pickle

@click.command()
@click.argument("sliced_model_path")
@click.option("-n","--project_name",type=str,default="debug")
@click.option("-o","--output",type=str)
@click.option("-i","--service_idle_detection",type=int,default=6000)
@click.option("-s","--startup_timeout",type=int,default=6000)

@click.option("-b","--model_test_batch_size",type=int,default=1)
@click.option("-r","--model_test_number_of_repeats",type=int,default=100)
@click.option("-d","--bandwidth_test_duration_sec",type=int,default=1)
@click.option("-l","--latency_test_count",type=int,default=1000)
@click.option("-m","--free_memory_multiplier",type=int,default=2)
#TODO: search constraints
def benchmark(
    sliced_model_path:str,
    project_name:str,
    output:str,
    service_idle_detection:int,
    startup_timeout:int,

    model_test_batch_size:int,
    model_test_number_of_repeats:int,
    bandwidth_test_duration_sec:int,
    latency_test_count:int,
    free_memory_multiplier:int
):
    logger = prepare_logger(DEBUG)
    logger.info("Loading Sliced Models...")
    pref = BenchmarkPreferences(
        service_idle_detection=service_idle_detection,
        split_strategy=SplitStrategy.from_str("scission"),
        logger=logger,
        startup_timeout=startup_timeout,

        model_test_batch_size=model_test_batch_size,
        model_test_number_of_repeats=model_test_number_of_repeats,
        bandwidth_test_duration_sec=bandwidth_test_duration_sec,
        latency_test_count=latency_test_count,
        free_memory_multiplier=free_memory_multiplier,
        project_name=project_name
    )
    try:
        sliced_models = None
        
        with open(sliced_model_path,"rb") as f:
            sliced_models = pickle.load(f)

        benchmark_result:BenchmarkResult = benchmark_slices(sliced_models,arg_preferences=pref)
        
        if(output is None):
            output = "benchmark.pickle"
        
        with open(output, "wb") as f:
            pickle.dump(benchmark_result,f,protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(f"Saving benchmark results as '{output}'")

    except Exception:
        logger.error(traceback.format_exc())
        exit(1)
    