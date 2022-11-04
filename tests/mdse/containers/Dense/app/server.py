from asyncore import write
import websockets, asyncio, signal
import os, functools, io
import keras as k
import numpy as np
from termcolor import colored

import logging

logger = logging.getLogger("websockets")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

m = k.models.load_model("/home/model")

async def forward(websocket):
    async for data in websocket:
        read_buff = io.BytesIO()
        read_buff.write(data)
        read_buff.seek(0)
        model_output = m.predict(np.load(read_buff,allow_pickle=True))
        write_buff = io.BytesIO()
        np.save(write_buff,model_output,allow_pickle=True)
        write_buff.seek(0)
        await websocket.send(write_buff)


async def backward(websocket):
    async for message in websocket:
        await websocket.send(f"Echo from backward: {message}")

tasks = {
    "forward": {
        "uri": "0.0.0.0",
        "port": 8765,
        "handler": forward,
        "ws": None
    },
    "backward": {
        "uri": "0.0.0.0",
        "port": 8766,
        "handler": backward,
        "ws": None
    }
}


for task,config in tasks.items():
    conn = websockets.serve(config["handler"],config["uri"],config["port"])
    tasks[task]["ws"] = conn

stop = asyncio.Future()
loop = asyncio.get_event_loop()
loop.run_until_complete(tasks["forward"]["ws"])
loop.run_until_complete(tasks["backward"]["ws"])
loop.add_signal_handler(signal.SIGTERM, stop.result, None)
loop.run_until_complete(stop)
    