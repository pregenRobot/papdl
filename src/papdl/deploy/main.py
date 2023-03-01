import click
from ..backend.common import prepare_logger
import logging


@click.command()
@click.argument("configuration_path")
def deploy(
    configuration_path:str
):
    logger = prepare_logger(logging.DEBUG)