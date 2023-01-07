import click
from .slice import main as slicer
from .configure import main as configurer

@click.group()
def main():
    pass

main.add_command(slicer.slice)
main.add_command(configurer.configure)
