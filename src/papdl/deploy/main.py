import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import click
from ..backend.common import prepare_logger
import logging
from ..configure.configure import Configuration,Configurer
import traceback
from .deploy import deploy_configuration
import dill as pickle


@click.command()
@click.argument("configuration_path")
@click.option("-d","--debug",type=bool,default=False)
def deploy(
    configuration_path:str,
    debug:bool
):
    try:
        logger = prepare_logger(logging.DEBUG)
        logging.info("Deploying models...")
        configuration:Configuration = None
        with open(configuration_path,"rb") as f:
            configuration = pickle.load(f)
        logger.info(configuration["blocks"])
        deploy_configuration(configuration,debug)
    except Exception:
        logger.error(traceback.format_exc())
        exit(1)