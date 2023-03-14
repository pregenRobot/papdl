import click
from .slice import main as slicer
from .configure import main as configurer
from .clean import main as cleaner
from .benchmark import main as benchmarker
from .deploy import main as deployer
import os


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

@click.group()
def main():
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    pass


main.add_command(slicer.slice)
main.add_command(configurer.configure)
main.add_command(cleaner.clean)
main.add_command(benchmarker.benchmark)
main.add_command(deployer.deploy)
