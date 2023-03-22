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
import uuid
from copy import deepcopy
import pandas as pd
import lz4.frame
from random import randint
from keras.datasets import cifar10

# model = apps.VGG16()
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

cifar10data = cifar10.load_data()

async def forward(websocket):
    i = 0
    async for data in websocket:
        deserialize_time = 0
        if i%4== 0:
            begin = time_ns()
            input_buff = io.BytesIO()
            input_buff.write(data)
            input_buff.seek(0)
            result = np.load(input_buff)
            requestId = result.dtype.names[1:][0]
            array = result["value"]
            end = time_ns()
            deserialize_time = end - begin
        elif i%4 == 1:
            begin = time_ns()
            input_buff = io.BytesIO()
            input_buff.write(data)
            input_buff.seek(0)
            requestId = input_buff.read(36).decode("utf-8")
            data = np.load(input_buff)
            end = time_ns()
            deserialize_time = end - begin
        elif i%4 == 2:
            begin = time_ns()
            input_buff = io.BytesIO()
            input_buff.write(data)
            input_buff.seek(0)
            uproot_stream = uproot.open(input_buff)
            requestId = uproot_stream["requestId"]
            data = uproot_stream["data"]["array"].array(library="np")
            end = time_ns()
            deserialize_time = end - begin
        elif i%4 == 3:
            begin = time_ns()
            decompressed_buff = io.BytesIO()
            decompressed_buff.write(lz4.frame.decompress(data))
            decompressed_buff.seek(0)
            requestId = decompressed_buff.read(36).decode("utf-8")
            data = np.load(decompressed_buff)
            end = time_ns()
            deserialize_time = end - begin
        
        i+=1
        await websocket.send(str(deserialize_time))
            
            
            
        
        
async def serve():
    async with ws_serve(ws_handler=forward,host="127.0.0.1",port=9999,read_limit=sys.maxsize,write_limit=sys.maxsize,max_size=sys.maxsize):
        await input()

def prepare_npfull_lz4(data,requestId):
    buff = io.BytesIO()
    buff.write(bytes(requestId,"utf-8"))
    np.save(buff,data)
    buff.seek(0)

    compressed_data = lz4.frame.compress(buff.read())

    # compressed_bytes = io.BytesIO()
    # compressed_bytes.write(compressed)
    # compressed_bytes.seek(0)
    # return buff
    compressed_bytes_io = io.BytesIO()
    compressed_bytes_io.write(compressed_data)
    compressed_bytes_io.seek(0)
    return compressed_bytes_io
    

def prepare_nprecarray(data,requestId):
    buff = io.BytesIO()
    data.dtype = [("value",float),(requestId,"V0")]
    np.save(buff, data)
    buff.seek(0)
    return buff
    
def prepare_npfull(data, requestId):
    buff = io.BytesIO()
    buff.write(bytes(requestId ,"utf-8"))
    np.save(buff, data)
    buff.seek(0)
    return buff

def prepare_uproot(data, requestId):
    buff = io.BytesIO()
    uproot_stream = uproot.recreate(buff)
    uproot_stream["requestId"] = requestId
    uproot_stream["data"] = {"array":data}
    buff.seek(0)
    return buff


        
async def input():
    async with ws_connect("ws://127.0.0.1:9999",read_limit=sys.maxsize,write_limit=sys.maxsize,max_size=sys.maxsize,logger=logging.LoggerAdapter(
                              logging.getLogger("websockets.erver"),None)) as websocket:
        rows = []
        for batch_size in range(1,11):
            for repeat in range(100):
                # random_input = np.random.random_sample((batch_size,224,224,3)).astype()
                index = randint(0,49_000)
                random_input = cifar10data[0][0][index:index+batch_size].astype(float)
                print(random_input.dtype,flush=True)

                requestId = str(uuid.uuid4())
                
                begin = time_ns()
                npfull_output_buff = prepare_npfull(deepcopy(random_input),requestId)
                end = time_ns()
                np_full_serialize_time =  end - begin

                begin = time_ns()
                uproot_buff = prepare_uproot(deepcopy(random_input),requestId)
                end = time_ns()
                uproot_serialize_time = end - begin
                

                begin = time_ns()
                nprecarray_output_buff = prepare_nprecarray(deepcopy(random_input),requestId)
                end = time_ns()
                nprecarray_serialize_time = end - begin
                
                begin = time_ns()
                npfull_lz4_output_buff = prepare_npfull_lz4(deepcopy(random_input),requestId)
                end = time_ns()
                npfull_lz4_serialize_time = end - begin
                
                begin = time_ns()
                await websocket.send(nprecarray_output_buff)
                end = time_ns()
                nprecarray_send_time = end - begin
                nprecarray_size = asizeof(nprecarray_output_buff)
                nprecarray_deserialize_time = await websocket.recv()
                
                begin = time_ns()
                await websocket.send(npfull_output_buff)
                end = time_ns()
                npfull_send_time = end - begin
                npfull_deserialize_time = await websocket.recv()
                np_full_size = asizeof(npfull_output_buff)
                
                begin = time_ns()
                await websocket.send(uproot_buff)
                end = time_ns()
                uproot_send_time = end - begin
                uproot_deserialize_time = await websocket.recv()
                uproot_size  = asizeof(uproot_buff)
                
                begin = time_ns()
                await websocket.send(npfull_lz4_output_buff)
                end = time_ns()
                npfull_lz4_send_time = end - begin
                npfull_lz4_deserialize_time = await websocket.recv()
                npfull_lz4_size = asizeof(npfull_lz4_output_buff)
                
                rows.append(["nprecarray", batch_size, nprecarray_serialize_time, int(nprecarray_deserialize_time), nprecarray_send_time, nprecarray_size])
                rows.append(["uproot", batch_size, uproot_serialize_time, int(uproot_deserialize_time), uproot_send_time, uproot_size ])
                rows.append(["npfull", batch_size, np_full_serialize_time, int(npfull_deserialize_time),npfull_send_time,np_full_size ])
                rows.append(["npfull_lz4", batch_size, npfull_lz4_serialize_time, int(npfull_lz4_deserialize_time),npfull_lz4_send_time,npfull_lz4_size ])
                print(f"Done batch_size: {batch_size} repeat: {repeat}",flush=True)

        result = pd.DataFrame(rows,columns=["method", "batch_size", "serialize_time","deserialize_time", "send_time", "payload_size"])
        with open("memory_test.csv","w+") as f:
            result.to_csv(f)
        print(result)
        
        
        
if __name__ == "__main__":
    asyncio.run(serve())
    
   
    