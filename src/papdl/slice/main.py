import click
from .slice import slice_model,slice_encode
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from keras.models import load_model
import traceback
from ..backend.common import prepare_logger
from logging import DEBUG


@click.command()
@click.argument("model_path")
@click.option("-o", "--output", default=None)
def slice(
        model_path: str,
        output:str = "slice.json"
):

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

    if(output is None):
        output="slices.json"

    try:
        # get_optimal_slices(sliced_model, pref)
        with open(output,"w") as f:
            f.write(slice_encode(sliced_model))
        logger.info(f"Saving sliced model list as '{output}'")
    except NotImplementedError:
        logger.error('Unknown split stretegy')
        exit(1)
