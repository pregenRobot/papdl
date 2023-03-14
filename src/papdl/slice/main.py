import click
from .slice import slice_model
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import traceback
from ..backend.common import prepare_logger
from logging import DEBUG
import keras
import dill as pickle


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
        model = keras.models.load_model(model_path)
    except Exception:
        logger.error(traceback.format_exc())
        exit(1)

    logger.info("Loading Model...")
    logger.info(model)
    logger.info("Slicing Model...")

    sliced_model = slice_model(model)

    if(output is None):
        output="slices.pickle"

    try:
        with open(output, "wb") as f:
            pickle.dump(sliced_model,f,protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(f"Saving sliced model list as '{output}'")
    except Exception as e:
        logger.error(traceback.format_exc())
        exit(1)
