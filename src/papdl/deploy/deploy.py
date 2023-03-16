
from ..configure.configure import Configuration,SliceBlock
from ..backend._api_deploy import PapdlService,PapdlSliceService,PapdlOrchestratorService
from ..backend.common import BenchmarkPreferences,prepare_logger,SplitStrategy
from ..backend.api_common import PapdlAPIContext
from logging import DEBUG
from typing import List
from docker.models.services import Service


def deploy_configuration(configuration:Configuration,debug:bool=False):
    
    logger = prepare_logger()
    
    bp = configuration["benchmark_preferences"]
    input_shape = configuration["input_shape"]
    pac = PapdlAPIContext(preference=bp)

    slice_services:List[PapdlSliceService] = [PapdlSliceService(pac,sb) for sb in configuration["blocks"]]
    
    orchestrator_service = PapdlOrchestratorService(pac,configuration)
    
    orchestrator_service.spawn(forward_service=slice_services[0],slices=slice_services,input_shape=input_shape)
    for i in range(len(slice_services)-1):
        curr:PapdlSliceService = slice_services[i]
        forward:PapdlSliceService = slice_services[i+1]
        curr.spawn(forward_service=forward,debug=debug)
    slice_services[-1].spawn(forward_service=orchestrator_service,debug=debug)
        
    logger.info("Issued service startup request")
    all_services = [*slice_services,orchestrator_service]
    s:Service
    for s in all_services:
        logger.info(s)
    
    