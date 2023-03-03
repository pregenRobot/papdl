
from ..configure.configure import Configuration
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
    
    spawned_services:List[PapdlSliceService] = [ss.spawn() for ss in slice_services]
    
    print([ss.service.attrs for ss in spawned_services])