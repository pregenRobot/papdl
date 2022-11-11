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
import time

logger = logging.getLogger("websockets")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

FORWARD_URL = os.getenv("FORWARD_URL")
FORWARD_PORT = 8765

m = k.models.load_model("/home/model")


class Wsc():
    def __init__(self,id:str,host:str,port:int):
        self.id = id
        self.host = host
        self.port = port
        self.conn: Union[ws.client.WebSocketProtocol,ws.server.WebSocketServerProtocol] = None
        self.connected:bool = False

    def serve(self,handler:Callable):
        if not self.connected:
            self.conn = ws.serve(handler,self.host,self.port)
            self.connected = True

    def connect(self):
        if not self.connected:
            self.conn = ws.connect(f"ws://{self.host}:{self.port}")
            self.connected = True

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
    "forward_in": Wsc("forward_in", FORWARD_URL,8765),
    "forward_out": Wsc("forward_out", FORWARD_URL, FORWARD_PORT)
}

async def forward(websocket):
    async for data in websocket:
        input = Wsc.read_np(data)
        output = m.predict(input)
        await conns["forward_out"].send(output)

forward_out_ws = None
while forward_out_ws is None:
    try:
        forward_out_ws = conns["forward_out"]
        forward_out_ws.connect()
        print(f"Connected to forward function: {forward_out_ws.conn}")
    except:
        print("Retrying outward connection in 3s...")

forward_in_ws = conns["forward_in"]
forward_in_ws.serve(forward)
        

stop = asyncio.Future()
loop = asyncio.get_event_loop()
loop.run_until_complete(forward_in_ws.conn)
loop.add_signal_handler(signal.SIGTERM, stop.result, None)
loop.run_until_complete(stop)
    