from websockets.client import connect as ws_connect
from websockets.server import serve as ws_serve
import gc
import numpy as np
import uproot
import io
import sys
import asyncio
from pympler.asizeof import asizeof
from time import time_ns
import logging

# model = apps.VGG16()
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

async def forward(websocket):
    async for data in websocket:
        begin = time_ns()
        input_buff = io.BytesIO()
        input_buff.write(data)
        input_buff.seek(0)
        input_arr = np.load(input_buff)
        output_buff = io.BytesIO()
        np.save(output_buff,input_arr)
        output_buff.seek(0)
        end = time_ns()
        print(f"Server processing time: {end - begin}",flush=True)
        begin = time_ns()
        await websocket.send(output_buff)
        end = time_ns()
        print(f"Server Send Time: {end - begin}",flush=True)
        
        
async def serve():
    async with ws_serve(ws_handler=forward,host="127.0.0.1",port=9999,read_limit=sys.maxsize,write_limit=sys.maxsize,max_size=sys.maxsize):
        await input()
        
async def input():
    async with ws_connect("ws://127.0.0.1:9999",read_limit=sys.maxsize,write_limit=sys.maxsize,max_size=sys.maxsize,logger=logging.LoggerAdapter(
                              logging.getLogger("websockets.erver"),None)) as websocket:
        random_input = np.random.random_sample((10,224,224,3))
        output_buff = io.BytesIO()
        np.save(output_buff,random_input)
        output_buff.seek(0)
        begin = time_ns()
        await websocket.send(output_buff)
        end = time_ns()
        print(f"Client send time {end - begin}",flush=True)
        begin = time_ns()
        result = await websocket.recv()
        end = time_ns()
        print(f"Client receive time {end - begin}",flush=True)
        
        
if __name__ == "__main__":
    asyncio.run(serve())
    
   
    