
import os

from websockets.client import connect as ws_connect
from websockets.server import serve as ws_serve
from websockets.datastructures import Headers,HeadersLike
from http import HTTPStatus
import numpy as np
import io
from typing import Optional,Dict,Tuple,Union
import logging
import asyncio
import traceback
from asyncio import Future
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'
from proto.iss_message_pb2 import IssMessage
import uuid

from websockets.legacy.client import Connect

from sanic import Request,Websocket,Sanic
from sanic import response


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
# forward_connection:Union[Connect,None] = None
# forward_url:Union[str,None] = None

CURR_HOST = "0.0.0.0"
CURR_HOST_PORT = 8765

app = Sanic("OrchestratorServer")
app.ctx.forward_url:str = None
app.ctx.forward_connection:Union[Connect,None] = None
app.ctx.rrm_lock = asyncio.Lock()
app.ctx.request_response_map:Dict[str,Future] = {}

# request_response_map:Dict[str,Future] = {}
# rrm_lock = asyncio.Lock()
@app.websocket("/predict")
async def record_response(request:Request,ws:Websocket):
    async for data in ws:
        try:
            iss_message_input = IssMessage()
            iss_message_input.ParseFromString(data)
            with app.ctx.rrm_lock:
                app.ctx.request_response_map[iss_message_input.requestId].set_result(iss_message_input.data)
        except Exception as e:
            logger.error(traceback.format_exc())
            with app.ctx.rrm_lock:
                app.ctx.request_response_map[iss_message_input.requestId].set_exception(e)
        
@app.get("/input")
async def make_prediction(request:Request):
    global forward_connection
    try:
        read_buff = io.BytesIO() 
        read_buff.write(request.body)
        read_buff.seek(0)
        data = np.load(read_buff,allow_pickle=True)
        requestId:str = uuid.uuid4()

        iss_message_output = IssMessage()
        iss_message_output.requestId = requestId
        iss_message_output.data = data

        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        with app.ctx.rrm_lock:
            app.ctx.request_response_map[requestId] = response_future
        forward_connection.send(iss_message_output.SerializeToString())
        await response_future
        
        response_np = response_future.result()
        write_buff = io.BytesIO()
        np.save(write_buff,response_np,allow_pickle=True)
        write_buff.seek(0)
        
        return response.raw(write_buff,status=HTTPStatus.OK)
        
        
    except Exception as e:
        logger.error(traceback.format_exc())
        return response.text("Unable to send input to next service",status=HTTPStatus.BAD_REQUEST)
        
@app.get("/forward")
async def configure_forward(request:Request):
    try:
        forward_url = request.headers.get("Forward-Url")
        app.ctx.forward_url:str = forward_url
        logger.info(f"Configured forward conection url: {forward_url}")
        return response.text("Configured forward connection url",status=HTTPStatus.OK)
    except:
        logger.error(traceback.format_exc())
        return response.text("Unable to configure forward url",status=HTTPStatus.BAD_REQUEST)

@app.get("/connect")
async def connect_to_forward(request:Request):
    try:
        app.ctx.forward_connection:Connect = await ws_connect(app.ctx.forward_url)
        logger.info(f"Successfly connected to forward_url: {app.ctx.forward_url}")
        return response.text("Configured forward url",status=HTTPStatus.OK)
    except:
        logger.error(traceback.format_exc())
        return response.text("Unable to connect to forward url")

@app.get("/healthcheck")
async def perform_healthcheck(request:Request):
    logger.info(f"Generating healthcheck")
    return response.json({"forward_url":app.ctx.forward_url, "connected": app.ctx.forward_connection is not None},status=HTTPStatus.OK)


if __name__ == "__main__":
    app.run(host=CURR_HOST,port=8765,access_log=False)