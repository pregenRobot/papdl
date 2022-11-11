import numpy as np
from typing import Callable
from websockets.client import connect as ws_connect
from websockets.server import serve as ws_serve

class Wsc():
    def __init__(self, id:str, host:str, port:int,logger):
        self.id = id
        self.host = host
        self.port = port
        self.conn = None
        self.connected:bool = False
        self.url = f"ws://{self.host}:{self.port}"
        self.server_logger = logger
    
    def serve(self,handler:Callable):
        if not self.connected:
            self.server_logger.info(f"Attempting to serve {self.url}")
            self.conn = ws_serve(handler,self.host,self.port)
            self.connected = True
            self.server_logger.info(f"Served {self.url}")
        
    async def connect(self):
        while not self.connected:
            try:
                self.server_logger.info(f"Attempting forward_out {self.url}")
                self.conn = await ws_connect(self.url)
                self.connected = True
                self.server_logger.info(f"Connected to {self.url}")
            except OSError as e:
                self.server_logger.info(e)
                self.server_logger.info(f"Reattempting forward_out {self.url}")
                sleep(1)

    async def send(self, array:np.ndarray):
        write_buff = io.BytesIO()
        np.save(write_buff, array, allow_pickle=True)
        write_buff.seek(0)
        await self.conn.send(write_buff)

    def read_np(data) -> np.ndarray:
        read_buff = io.BytesIO()
        read_buff.write(data)
        read_buff.seek(0)
        return np.load(read_buff,allow_pickle=True)
    
    def close(self):
        self.conn.close()
