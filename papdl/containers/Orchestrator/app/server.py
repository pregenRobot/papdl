import os, functools, io
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'

import asyncio, signal
# import websockets.serve
from websockets.server import serve as ws_serve
from websocket import create_connection as ws_conn
import websockets as ws
import keras as k
import numpy as np
import logging
import os
from typing import *
from time import sleep

# logger = logging.getLogger("websockets")
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

server_logger = logging.getLogger("server")
server_logger_handler:logging.StreamHandler = logging.StreamHandler()
server_logger_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(name)-6s] %(levelname)-8s %(message)s"
))
server_logger.addHandler(server_logger_handler)
server_logger.setLevel(logging.DEBUG)

FORWARD_URL = os.getenv("FORWARD_URL")
FORWARD_PORT = 8765

class Wsc():
    def __init__(self, id:str, host:str, port:int):
        self.id = id
        self.host = host
        self.port = port
        self.conn = None
        self.connected:bool = False
        self.url = f"ws://{self.host}:{self.port}"
    
    def serve(self,handler:Callable):
        if not self.connected:
            server_logger.info(f"Attempting to serve {self.url}")
            self.conn = ws_serve(handler,self.host,self.port)
            self.connected = True
            server_logger.info(f"Served {self.url}")
    
    async def connect(self):
        while not self.connected:
            try:
                server_logger.info(f"Attempting forward_out {self.url}")
                self.conn = await ws.connect(self.url)
                self.connected = True
                server_logger.info(f"Connected to {self.url}")
            except OSError as e:
                server_logger.info(e)
                server_logger.info(f"Reattempting forward_out {self.url}")
                sleep(5)
    
    async def send(self, array:np.ndarray):
        write_buff = io.BytesIO()
        np.save(write_buff, array, allow_pickle=True)
        write_buff.seek(0)
        async with self.conn as conn:
            await conn.send(write_buff)
        # self.conn.send(write_buff)

    def read_np(data) -> np.ndarray:
        read_buff = io.BytesIO()
        read_buff.write(data)
        read_buff.seek(0)
        return np.load(read_buff,allow_pickle=True)
    
    def close(self):
        self.conn.close()

conns = {
    "forward_in" : Wsc("forward_in", "0.0.0.0", 8765),
    "forward_out": Wsc("forward_out", FORWARD_URL, FORWARD_PORT)
}

async def forward(messages):
    async for data in messages:
        result = Wsc.read_np(data)
        server_logger.info(result)


# async def send_random_data():
#     await conns["forward_out"].connect()
#     while True:
#         server_logger.info("Sending data...")
#         sample = np.random.random((1,100))
#         await conns["forward_out"].send(sample)
#         sleep(1)

async def send_random_data():
    wsc = conns["forward_out"]
    async with ws.connect(wsc.url) as conn:
        for i in range (1000):
            server_logger.info("Sending data...")
            sample = np.random.random((1,100))
            
            write_buff = io.BytesIO()
            np.save(write_buff,sample, allow_pickle=True)
            write_buff.seek(0)
            await conn.send(write_buff)
        


conns["forward_in"].serve(forward)
stop = asyncio.Future()
loop = asyncio.get_event_loop()
loop.run_until_complete(conns["forward_in"].conn)
loop.run_until_complete(send_random_data())

loop.add_signal_handler(signal.SIGTERM, stop.result, None)
loop.run_until_complete(stop)