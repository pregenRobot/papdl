
from ..configure.configure import Configuration,SliceBlock
from ..backend._api_deploy import PapdlService,PapdlSliceService,PapdlOrchestratorService
from ..backend.common import BenchmarkPreferences,prepare_logger,SplitStrategy
from ..backend.api_common import PapdlAPIContext
from logging import DEBUG
from typing import List


def deploy_configuration(configuration:Configuration):
    
    bp = BenchmarkPreferences(
        service_idle_detection=600,
        startup_timeout=600,
        split_strategy=SplitStrategy.from_str("scission"),
        logger=prepare_logger(DEBUG)
    )

    pac = PapdlAPIContext(preference=bp)

    slice_services:List[PapdlSliceService] = [PapdlSliceService(pac,sb) for sb in configuration["blocks"]]
    
    orchestrator_service = PapdlOrchestratorService(pac,configuration)
    
    print(slice_services)
    print(orchestrator_service)
    
    orchestrator_service.spawn(forward_service=slice_services[0],slices=slice_services)
    for i in range(len(slice_services)-1):
        curr:PapdlSliceService = slice_services[i]
        forward:PapdlSliceService = slice_services[i+1]
        curr.spawn(forward_service=forward)
    slice_services[-1].spawn(forward_service=orchestrator_service)
        
    print([ss.service.attrs for ss in slice_services])
    
    print(orchestrator_service.service.attrs)