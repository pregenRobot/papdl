import click
from .slice import slice_model
from keras.models import load_model

@click.command()
@click.argument("model_path")
@click.option("-o", "--output", default=None)
@click.option("-x", "--optimiser", default="atomic")
@click.option("-a", "--optimiserargs", default=None)
def slice(model_path:str, output:str, optimiser:str, optimiserargs):
    print(f"Slicing model {model} to location {output} optimized with {optimiser} having {optimiserargs}")
    
    model = load_model(model_path)
    print("Loaded Model...")
    print(model)
    print("Slicing Model")
    print(slice_model(model))
    
    