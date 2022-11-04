from asyncore import write
import websockets, asyncio, signal
import os, functools, io
import keras as k
import numpy as np
from termcolor import colored
import logging
import os

logger = logging.getLogger("websockets")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

BACKWARD_URL = os.getenv["BACKWARD_URL"]
BACKWARD_PORT = int(os.getenv["BACKWARD_PORT"])
FORWARD_URL = os.getenv["FORWARD_URL"]
FORWARD_PORT = int(os.getenv["BACKWARD_PORT"])



async def forward(websocket):
    async for data in websocket:
        read_buff = io.BytesIO()
        read_buff.write(data)
        read_buff.seek(0)
        model