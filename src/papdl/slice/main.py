import click

@click.command()
@click.argument("model")
@click.option("-o", "--output", default=None)
@click.option("-x", "--optimiser", default="atomic")
@click.option("-a", "--optimiserargs", default=None)
def slice(model:str, output:str, optimiser:str, optimiserargs):
    print(f"Slicing model {model} to location {output} optimized with {optimiser} having {optimiserargs}")