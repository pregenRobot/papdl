import os, functools, io
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'

from asyncore import write
import asyncio, signal
import websockets as ws
import keras as k
import numpy as np
from termcolor import colored
import logging
import os
from typing import *
from time import sleep

logger = logging.getLogger("websockets")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

FORWARD_URL = os.getenv("FORWARD_URL")
FORWARD_PORT = 8765

class Wsc():
    def __init__(self,id:str,host:str,port:int):
        self.id = id
        self.host = host
        self.port = port
        self.conn: Union[ws.client.WebSocketProtocol,ws.server.WebSocketServerProtocol] = None
    def serve(self,handler:Callable):
        self.conn = ws.serve(handler,self.host,self.port)
    def connect(self):
        self.conn = ws.connect(f"ws://{self.host}:{self.port}")
    async def send(self,array:np.ndarray):
        write_buff = io.BytesIO()
        np.save(write_buff,array,allow_pickle=True)
        write_buff.seek(0)
        return await self.conn.send(write_buff)
    def read_np(data) -> np.ndarray:
        read_buff = io.BytesIO()
        read_buff.write(data)
        read_buff.seek(0)
        return np.load(read_buff,allow_pickle=True)
    def close(self):
        self.conn.close()

conns = {
    "forward_in": Wsc("forward_in",FORWARD_URL,8765),
    "forward_out": Wsc("forward_out",FORWARD_URL,FORWARD_PORT)
}

async def forward(websocket):
    async for data in websocket:
        result = Wsc.read_np(data)
        print(result)

conns["forward_in"].serve(forward)
conns["forward_out"].connect()

async def send_random_data():
    # samples = np.random.random((1000,100))
    while True:
        sample = np.random.random((1,100))
        conns["forward_out"].send(sample)
        sleep(1)
    # for s in samples:
    #     conns["forward_out"].send(s)

stop = asyncio.Future()
loop = asyncio.get_event_loop()
loop.run_until_complete(send_random_data())
loop.add_signal_handler(signal.SIGTERM, stop.result, None)
loop.run_until_complete(stop)

# asyncio.get_event_loop().run_forever(send_random_data)

