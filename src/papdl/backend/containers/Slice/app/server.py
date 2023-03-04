

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
        logger.info("Received INPUT!")
        try:
            input_buff = io.BytesIO()
            input_buff.write(data)
            input_buff.seek(0)

            input_uproot_buff = uproot.open(input_buff)
            logger.info("Received INPUT!")
            model_input = input_uproot_buff["data"]["array"].array(library="np")
            logger.info(model_input)
            model_output = model.predict(model_input)
            logger.info(model_output)
            
            output_buff = io.BytesIO()
            output_uproot_buff = uproot.recreate(output_buff)
            output_uproot_buff["data"] = {"array":model_output}
            output_uproot_buff["requestId"] = str(input_uproot_buff["requestId"])

            output_buff.seek(0)
            await forward_connection.send(output_buff)
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
            forward_connection = await ws_connect(fwu,open_timeout=None)
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
    async with  ws_serve(ws_handler=forward, host=CURR_HOST,port=CURR_HOST_PORT,logger=logger,process_request=process_request):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(serve())
