from websockets.client import connect as ws_connect
from websockets.server import serve as ws_serve
import gc
import keras.applications as apps
import numpy as np
import uproot
import io
import sys
import asyncio
from pympler.asizeof import asizeof


model = apps.VGG16()

async def forward(websocket):
    async for data in websocket:
        input_buff = io.BytesIO()
        input_buff.write(data)
        input_buff.seek(0)

        input_uproot_buff = uproot.open(input_buff)
        model_input = input_uproot_buff["data"]["array"].array(library="np")
        
        output_buff = io.BytesIO()
        output_uproot_buff = uproot.recreate(output_buff)
        output_uproot_buff["data"] = {"array":model_input}

        output_buff.seek(0)
        await websocket.send(output_buff)
        
        
async def serve():
    async with ws_serve(ws_handler=forward,host="127.0.0.1",port=9999,read_limit=sys.maxsize,write_limit=sys.maxsize,max_size=sys.maxsize):
        await input()
        
async def input():
    async with ws_connect("ws://127.0.0.1:9999",read_limit=sys.maxsize,write_limit=sys.maxsize,max_size=sys.maxsize) as websocket:
        random_input = np.random.random_sample((10,224,224,3))
        output_buff = io.BytesIO()
        uproot_buff = uproot.recreate(output_buff)
        uproot_buff["data"] = {"array":random_input}
        output_buff.seek(0)
        await websocket.send(output_buff)
        result = await websocket.recv()

        input_buff = io.BytesIO()
        input_buff.write(result)
        uproot_input_buff = uproot.open(input_buff)
        output = uproot_input_buff["data"]["array"].array(library="np")
        
        
if __name__ == "__main__":
    asyncio.run(serve())
    
   
    