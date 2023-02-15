from docker.models.nodes import Node
from docker.models.images import Image
from docker.models.services import Service
from docker.models.secrets import Secret
from docker.types import RestartPolicy,EndpointSpec,SecretReference,NetworkAttachmentConfig

from .api_common import PapdlAPIContext,get_papdl_service,get_papdl_secret
from .common import Slice,AppType
from typing import List,TypedDict,Tuple,Dict
from os import path,mkdir,PathLike
from random import randint
from OpenSSL import crypto
from copy import deepcopy
import sys
from pathlib import Path

class PapdlRegistryAPI:
    def __init__(self,context:PapdlAPIContext):
        self.context = context
    
    def cert_gen(self,cert_path:PathLike, key_path:PathLike):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 4096)
        cert = crypto.X509()
        cert.get_subject().C = self.cert_specs["C"]
        cert.get_subject().ST = self.cert_specs["ST"]
        cert.get_subject().L = self.cert_specs["L"]
        cert.get_subject().O = self.cert_specs["O"]
        cert.get_subject().OU = self.cert_specs["OU"]
        cert.get_subject().CN = self.cert_specs["CN"]
        cert.get_subject().emailAddress = self.cert_specs["emailAddress"]
        cert.set_serial_number(randint(1,sys.maxsize - 1))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(self.cert_specs["validity_seconds"])
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k,'sha256')

        with open(cert_path, "wt") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
        
        with open(key_path, "wt") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))
    
    def secret_gen(self)->Tuple[Secret,Secret]:
        cert_path = path.join(self.context.dircontext["api_module_path"],"certificates","registry.crt")
        key_path = path.join(self.context.dircontext["api_module_path"],"certificates","registry.key")
        if(not(Path(cert_path).is_file() and Path(key_path).is_file())):
            self.cert_gen(cert_path,key_path)
        
        registry_docker_cert = get_papdl_secret(self.context,labels={"type":"cert"},name="registry.crt")
        registry_docker_key = get_papdl_secret(self.context,labels={"type":"key"},name="registry.key")
        
        registry_crt:Secret=None
        if(len(registry_docker_cert) == 0):
            with open(cert_path, "rb") as f:
                cert_data = f.read()
                registry_crt = self.context.client.secrets.create(name="registry.crt",data=cert_data,labels={"papdl":"true","type":"cert"})
        else:
            registry_crt = registry_docker_cert[0]

        registry_key:Secret=None
        if(len(registry_docker_key) == 0):
            with open(key_path, "rb") as f:
                key_data = f.read()
                registry_key = self.context.client.secrets.create(name="registry.key",data=key_data,labels={"papdl":"true","type":"key"})
        else:
            registry_key = registry_docker_key[0]
        
        return registry_crt,registry_key
    
    def assign_registry_node(self):
        manager_node = self.context.client.nodes.list(filters={'role':"manager"})[0]
        manager_node_spec = deepcopy(manager_node.attrs["Spec"])
        manager_node_spec["Labels"]["registry"] = 'true'
        manager_node.update(manager_node_spec)
    
    def spawn_registry(self)->Service:
        self.assign_registry_node()
        registry_services = get_papdl_service(self.context,labels={"type":"registry"})
        if(len(registry_services) != 0):
            return registry_services[0]
        
        self.context.logger.info(f"Spawning Registry service...")
        self.context.loadingBar.start()
        self.context.client.images.pull("registry",tag="latest")
        crt,key= self.secret_gen()
        registry_volume_path = path.join(self.context.dircontext["api_module_path"], "registry_volume")
        endpoint_spec = EndpointSpec(ports={443:443})
        
        sr_crt = SecretReference(secret_id=crt.id,secret_name=crt.name)
        sr_key = SecretReference(secret_id=key.id,secret_name=key.name)
        rp = RestartPolicy(condition="any")
        nac = NetworkAttachmentConfig(self.context.network.name)
        
        service = self.context.client.services.create(
            image="registry",
            name="registry",
            constraints=[f"node.labels.registry==true"],
            mounts=[f"{registry_volume_path}:/var/lib/registry"],
            env=[
                "REGISTRY_HTTP_ADDR=0.0.0.0:443",
                "REGISTRY_HTTP_TLS_CERTIFICATE=/run/secrets/registry.crt",
                "REGISTRY_HTTP_TLS_KEY=/run/secrets/registry.key",
            ],
            secrets=[sr_crt,sr_key],
            maxreplicas=1,
            endpoint_spec=endpoint_spec,
            networks=[nac],
            labels={
                "papdl":"true",
                "type":"registry"
            },
            restart_policy=rp
        )
        self.context.loadingBar.stop()
        return service
        
        