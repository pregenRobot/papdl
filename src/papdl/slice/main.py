import click
from .slice import slice_model, Slice
from keras.models import load_model
import traceback
from ..benchmark.main import get_optimal_slices,SplitStrategy
from typing import List

@click.command()
@click.argument("model_path")
@click.option("-o", "--output", default=None)
@click.option("-x", "--strategy", default="scission")
@click.option("-a", "--strategyargs", default=None)
def slice(
    model_path:str,
    output:str,
    strategy:str,
    strategyargs:str):
    print(f"Slicing model {model_path} to location {output} with strategy {strategy} having {strategyargs}")
    
    model = None
    try:
        model = load_model(model_path)
    except Exception:
        print(traceback.format_exc())
        exit(1)

    print("Loading Model...")
    print(model)
    print("Slicing Model")
    sliced_model = slice_model(model)
    
    print("Calculating Optimal slices") 
    try:
        get_optimal_slices(sliced_model,SplitStrategy.from_str(strategy))
    except NotImplementedError:
        print('Unknown split stretegy')
        exit(1)
    
    
    