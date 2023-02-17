import click
from .slice import main as slicer
from .configure import main as configurer
from .clean import main as cleaner
import os


@click.group()
def main():
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    pass


main.add_command(slicer.slice)
main.add_command(configurer.configure)
main.add_command(cleaner.clean)
