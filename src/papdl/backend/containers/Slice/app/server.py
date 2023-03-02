

from time import sleep
import os

from websockets.client import connect as ws_connect
from websockets.server import serve as ws_serve
from websockets.datastructures import Headers,HeadersLike
from http import HTTPStatus

import numpy as np
import io
from typing import Optional,Dict,Tuple
import logging
import asyncio
from keras.models import load_model
from keras import Model
import getpass

os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'



def prepare_logger()->logging.Logger:
    logger = logging.getLogger("server")
    server_logger_handler: logging.StreamHandler = logging.StreamHandler()
    server_logger_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)-6s] %(levelname)-8s %(message)s"
                            ))
    logger.addHandler(server_logger_handler)
    logger.setLevel(logging.DEBUG)
    return logger
    
logger = prepare_logger()
forward_connection = None
forward_url = None
model:Model = load_model(f"/home/{getpass.getuser()}/model")
model.compile()

CURR_HOST = "0.0.0.0"
CURR_HOST_PORT =  8765


async def send(array:np.ndarray):
    write_buff = io.BytesIO()
    np.save(write_buff,array,allow_pickle=True)
    write_buff.seek(0)
    if forward_connection is None:
        logger.error("Forward connection has not been established. Dropping input...")
    else:
        await forward_connection.send(model.predict(write_buff))

async def forward(websocket):
    async for data in websocket:
        read_buff = io.BytesIO()
        read_buff.write(data)
        read_buff.seek(0)
        output = model.predict(np.load(read_buff,allow_pickle=True))

        write_buff = io.BytesIO()
        np.save(write_buff,output,allow_pickle=True)
        write_buff.seek(0)
        await forward_connection.send(write_buff)

async def process_request(path:str,request_headers:Headers)->Optional[Tuple[HTTPStatus,HeadersLike,bytes]]:
    global forward_connection
    if forward_connection is None:
        forward_url = request_headers.get("Forward-Url")
        try:
            forward_connection = await ws_connect(forward_url)
            logger.info(f"Successfully connected to forward_url: {forward_url}")
            return (HTTPStatus.OK,{},b"")
        except:
            logger.error(f"Failed to connect to  forward_url: {forward_url}")
            return (HTTPStatus.BAD_REQUEST,{},bytes(f"Failed to connect to forward_url: {forward_url}\n","utf-8"))
            
    else:
        return None

async def serve():
    logger.info("Attempting to serve current websocket server...")
    async with  ws_serve(ws_handler=forward, host=CURR_HOST,port=CURR_HOST_PORT,logger=logger,process_request=process_request):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(serve())
