import click
from ..backend.api_common import PapdlAPIContext,get_papdl_service,get_papdl_image,get_papdl_network,get_papdl_secret


@click.option("-b","--benchmark_images",show_default=True,is_flag=True, flag_value=True)
@click.option("-B","--benchmark_services",show_default=True,is_flag=True, flag_value=True)
@click.option("-s","--slice_images",show_default=True,is_flag=True, flag_value=True)
@click.option("-S","--slice_services",show_default=True,is_flag=True, flag_value=True)
@click.option("-R","--registry_service",show_default=True,is_flag=True, flag_value=True)
@click.option("-I","--iperf_services",show_default=True,is_flag=True, flag_value=True)
@click.option("-n","--network",show_default=True,is_flag=True, flag_value=True)
@click.option("-x","--secrets",show_default=True,is_flag=True, flag_value=True)
@click.command()
def clean(
    benchmark_images:bool,
    benchmark_services:bool,
    slice_images:bool,
    slice_services:bool,
    registry_service:bool,
    iperf_services:bool,
    network:bool,
    secrets:bool,
    
):
    pac = PapdlAPIContext()
    print(benchmark_images,benchmark_services,slice_images,slice_services,registry_service,iperf_services,network,secrets)
    

    [print(i.id.split(":")[1]) for i in get_papdl_image(pac)]

    if(benchmark_images):
        [i.remove(force=True) for i in get_papdl_image(pac,labels={"type":"benchmark"})]
    if(benchmark_services):
        [s.remove() for s in get_papdl_service(pac,labels={"type":"benchmark"})]
    if(slice_images):
        [i.remove(force=True) for i in get_papdl_image(pac,labels={"type":"slice"})]
    if(slice_services):
        [s.remove() for s in get_papdl_service(pac,labels={"type":"slice"})]
    if(registry_service):
        [s.remove() for s in get_papdl_service(pac,labels={"type":"registry"})]
    if(iperf_services):
        [s.remove() for s in get_papdl_service(pac,labels={"type":"iperf"})]
    if(network):
        [n.remove() for n in get_papdl_network(pac)]
    if(secrets):
        [s.remove() for s in get_papdl_secret(pac)]