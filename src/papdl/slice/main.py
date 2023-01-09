import click
from .slice import slice_model
from keras.models import load_model
import traceback
from ..benchmark.main import get_optimal_slices
from ..backend.common import SplitStrategy,Preferences, prepare_logger
from logging import DEBUG


@click.command()
@click.argument("model_path")
@click.option("-o", "--output", default=None)
@click.option("-x", "--strategy", default="scission")
@click.option("-a", "--strategyargs", default=None)
def slice(
    model_path:str,
    output:str,
    strategy:str,
    strategyargs:str):
    
    model = None
    logger = prepare_logger(DEBUG)
    try:
        model = load_model(model_path)
    except Exception:
        logger.error(traceback.format_exc())
        exit(1)

    logger.info("Loading Model...")
    logger.info(model)
    logger.info("Slicing Model...")
    
    sliced_model = slice_model(model)
    
    pref = Preferences(
        service_idle_detection=100,
        split_strategy=SplitStrategy.from_str(strategy),
        logger=logger
    )
    
    logger.info(f"Calculating Optimal slices with pref: {pref}...") 

    try:
        get_optimal_slices(sliced_model, pref)
    except NotImplementedError:
        logger.error('Unknown split stretegy')
        exit(1)
    
    
    