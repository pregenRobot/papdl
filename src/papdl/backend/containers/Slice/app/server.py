
import sys
from time import sleep
import os
import json


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
import traceback
import uproot
import gc

os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'

def isDebug()->bool:
    return int(os.environ.get("DEBUG")) == 1


def prepare_logger()->logging.Logger:
    logger = logging.getLogger("server")
    server_logger_handler: logging.StreamHandler = logging.StreamHandler()
    server_logger_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)-6s] %(levelname)-8s %(message)s"
                            ))
    logger.addHandler(server_logger_handler)
    logger.setLevel(logging.DEBUG)

    if isDebug():
        logging.getLogger("websockets").addHandler(logging.NullHandler())
        logging.getLogger('asyncio').setLevel(logging.ERROR)
        logging.getLogger('asyncio.coroutines').setLevel(logging.ERROR)
        logging.getLogger('websockets.server').setLevel(logging.ERROR)
        logging.getLogger('websockets.protocol').setLevel(logging.ERROR)
        logger.propagate = False
    return logger
    
def get_next_url()->str:
    forward_service_name = os.environ.get("FORWARD")
    return f"ws://{forward_service_name}:8765"

    
logger = prepare_logger()
forward_connection = None
forward_url = get_next_url()
model:Model = load_model(f"/home/{getpass.getuser()}/model")
model.compile()

CURR_HOST = "0.0.0.0"
CURR_HOST_PORT =  8765


async def forward(websocket):
    async for data in websocket:
        try:
            input_buff = io.BytesIO()
            input_buff.write(data)
            input_buff.seek(0)
            input_array = np.load(input_buff)
            
            requestId = input_array.dtype.names[1:][0]
            model_output = model.predict(input_array.view(np.recarray).value)
            model_output.dtype = [("value",float),(requestId,"V0")]

            output_buff = io.BytesIO()
            np.save(output_buff,model_output)
            output_buff.seek(0)
            await forward_connection.send(output_buff)
            gc.collect()
        except:
            logger.error("Caught Exception! Dropping input...")
            logger.error(traceback.format_exc())

async def process_request(path:str,request_headers:Headers)->Optional[Tuple[HTTPStatus,HeadersLike,bytes]]:
    global forward_connection
    global forward_url
    
    # Continue with prediction
    logger.info(f"path={path}")
    logger.info(f"request_headers={request_headers}")

    try:
        if path == "/predict":
            return None
        
        if path == "/connect":
            logger.info(f"Attempting to connect to forward_url: {forward_url}/predict")
            fwu = f"{forward_url}/predict"
            forward_connection = await ws_connect(fwu,open_timeout=None,max_size=sys.maxsize,read_limit=sys.maxsize,write_limit=sys.maxsize)
            logger.info(f"Successfully connected to forward_url: {fwu}")
            return (HTTPStatus.OK,{},b"")
        
        if path == "/healthcheck":
            logger.info("Generating healthcheck")
            return (HTTPStatus.OK, {}, bytes(json.dumps({
                "forward_url":forward_url,
                "connected": forward_connection is not None and forward_connection.open,
                "model_name":model.name
            }),"utf-8"))
    except Exception as e:
        fe = traceback.format_exc()
        logger.error(fe)
        return (HTTPStatus.BAD_REQUEST,{},bytes(str(fe),"utf-8"))

async def serve():
    logger.info("Attempting to serve current websocket server...")
    configuration = {
        "ws_handler":forward,
        "host":CURR_HOST,
        "port":CURR_HOST_PORT,
        "process_request":process_request,
        "read_limit":sys.maxsize,
        "max_size":sys.maxsize,
        "write_limit":sys.maxsize
    }
    if isDebug():
        configuration["logger"] = logger
    async with  ws_serve(**configuration):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(serve())
