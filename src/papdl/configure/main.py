import click


@click.command()
@click.argument("model")
@click.option("-n", "network", default="local")
@click.option("-o", "output", default=None)
def configure(model, network, output):
    print(f"Generating configuration for {model} with {network} to {output}")
