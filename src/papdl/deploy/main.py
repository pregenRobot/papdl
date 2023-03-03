import click
from ..backend.common import prepare_logger
import logging
from ..configure.configure import Configuration,Configurer
import traceback
from .deploy import deploy_configuration


@click.command()
@click.argument("configuration_path")
def deploy(
    configuration_path:str
):
    logger = prepare_logger(logging.DEBUG)
    logging.info("Deploying models...")
    
    try:
        configuration:Configuration = None
        with open(configuration_path, "r") as f:
            json_str = f.read()
            configuration = Configurer.decode_configuration(json_str)
        deploy_configuration(configuration)
    except Exception:
        logger.error(traceback.format_exc())
        exit(1)