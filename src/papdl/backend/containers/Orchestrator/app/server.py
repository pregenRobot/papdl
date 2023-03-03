
import os
import json

from websockets.client import connect as ws_connect
from websockets.server import serve as ws_serve
from websockets.datastructures import Headers,HeadersLike
from http import HTTPStatus
import numpy as np
import io
from typing import Optional,Dict,Tuple,Union,List
import logging
import asyncio
import traceback
from asyncio import Future
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'
from proto.iss_message_pb2 import IssMessage
import uuid
import requests

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

def get_next_url()->str:
    forward_service_name = os.environ.get("FORWARD")
    logger.info(f"Loaded forward url: {forward_service_name}")
    return f"ws://{forward_service_name}:8765"

def get_all_slices()->List[str]:
    service_list = os.environ.get("SLICES").split(",")
    logger.info(f"Loaded slice services: {service_list}")
    return service_list

app = Sanic("OrchestratorServer")
app.ctx.forward_url:str = get_next_url()
app.ctx.all_slice_services:List[str] = get_all_slices()
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
        # read_buff = io.BytesIO() 
        # read_buff.write(request.body)
        # read_buff.seek(0)
        # data = np.load(read_buff,allow_pickle=True)
        input_shape = (100,)
        batch_size = 1000
        dimensions = (batch_size,) + input_shape
        data = np.random.random_sample(dimensions)
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

@app.get("/connect")
async def connect_to_forward(request:Request):
    try:
        app.ctx.forward_connection:Connect = await ws_connect(f"{app.ctx.forward_url}/predict")
        logger.info(f"Successfly connected to forward_url: {app.ctx.forward_url}")
        return response.text("Successfully connected to  forward url",status=HTTPStatus.OK)
    except:
        logger.error(traceback.format_exc())
        return response.text("Unable to connect to forward url")

@app.get("/activate")
async def activate_all_slices(request:Request):
    try:
        result = {}
        service_name:str
        for service_name in app.ctx.all_slice_services:
            slice_forward_connect_url = f"http://{service_name}:8765/connect"
            connect_resp = requests.get(slice_forward_connect_url)
            logger.info(f"Received {connect_resp} from service {service_name}")
            result[service_name] = {
                "status":connect_resp.status_code,
                "response":connect_resp.text
            }
        return response.json(result,status=HTTPStatus.OK) 
    except Exception:
        logger.error(traceback.format_exc())
        return response.text(body="Failed to activate one or all slice nodes",status=HTTPStatus.BAD_REQUEST)


@app.get("/healthcheck")
async def perform_healthcheck(request:Request):
    logger.info(f"Generating healthcheck")
    return response.json({"forward_url":app.ctx.forward_url, "connected": app.ctx.forward_connection is not None and app.ctx.forward_connection.open},status=HTTPStatus.OK)


@app.get("/workerhealthcheck")
async def queryworker_healthcheck(request:Request):
    try:
        logger.info(f"Generating worker healthcheck")
        result = {}
        service_name:str
        for service_name in app.ctx.all_slice_services:
            healthcheck_url = f"http://{service_name}:8765/healthcheck"
            health_resp = requests.get(healthcheck_url)
            result[service_name] = {
                "status":health_resp.status_code,
                "response": health_resp.json()
            }
            
        return response.json(result,status=HTTPStatus.OK)
    except Exception:
        logger.error(traceback.format_exc())
        return response.text(body="Failed to fetch health check for one or more workers. Perhaps connections have not been established yet. Run http://\{orchestrator_ip\}:8765/activateworkers",status=HTTPStatus.BAD_REQUEST)


if __name__ == "__main__":
    app.run(host=CURR_HOST,port=8765,access_log=False)