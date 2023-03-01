import click
from ..slice.slice import slice_decode
from ..backend.common import prepare_logger,BenchmarkPreferences
from ..benchmark.benchmark import benchmark_slices,SplitStrategy,encode_benchmark_result,decode_benchmark_result,BenchmarkResult
from logging import DEBUG
import traceback

@click.command()
@click.argument("sliced_model_path")
@click.option("-o","--output")
@click.option("-i","--service_idle_detection")
@click.option("-s","--startup_timeout")
#TODO: search constraints
def benchmark(
    sliced_model_path:str,
    output:str,
    service_idle_detection:int,
    startup_timeout:int,
):
    logger = prepare_logger(DEBUG)
    logger.info("Loading Sliced Models...")


    # pref = Preferences(
    #     service_idle_detection=600,
    #     split_strategy=SplitStrategy.from_str(strategy),
    #     logger=logger,
    #     startup_timeout=600,
    #     search_constraints=SearchConstraints(
    #         layer_must_be_in_device={},
    #         layer_must_not_be_in_device={}
    #     )
    # )
    # logger.info(f"Calculating Optimal slices with pref: {pref}...")
    
    
    if service_idle_detection is None:
        service_idle_detection = 600
    
    if startup_timeout is None:
        startup_timeout = 600
        
    pref = BenchmarkPreferences(
        service_idle_detection=service_idle_detection,
        split_strategy=SplitStrategy.from_str("scission"),
        logger=logger,
        startup_timeout=startup_timeout
    )

    try:
        sliced_models = None
        
        with open(sliced_model_path,"r") as f:
            json_str = f.read()
            sliced_models = slice_decode(json_str)

        benchmark_result:BenchmarkResult = benchmark_slices(sliced_models,arg_preferences=pref)
        
        if(output is None):
            output = "benchmark.json"
        
        with open(output,"w") as f:
            f.write(encode_benchmark_result(benchmark_result))

    except Exception:
        logger.error(traceback.format_exc())
        exit(1)
    