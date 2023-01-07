import click
from .slice import slice_model
from .slice import SplitStrategy, Slice
from keras.models import load_model
import traceback

@click.command()
@click.argument("model_path")
@click.option("-o", "--output", default=None)
@click.option("-x", "--optimiser", default="atomic")
@click.option("-a", "--optimiserargs", default=None)
def slice(model_path:str, output:str, optimiser:str, optimiserargs:str):
    print(f"Slicing model {model_path} to location {output} optimized with {optimiser} having {optimiserargs}")
    
    try:
        model = load_model(model_path)
        print("Loaded Model...")
        print(model)
        print("Slicing Model")
        # print(slice_model(model, SplitStrategy.ATOMIC))
        for slice in slice_model(model, SplitStrategy.ATOMIC):
            slice.model.summary()
    except Exception:
        print(traceback.format_exc())
        exit(1)
    
    
    