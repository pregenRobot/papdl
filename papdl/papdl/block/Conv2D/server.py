from asyncore import write
import websockets, asyncio, signal
import os, functools, io
import keras as k
import numpy as np

FRONT_HOST = os.getenv("FRONT_HOST")
FRONT_PORT = os.getenv("FRONT_PORT")
BACK_HOST = os.getenv("BACK_HOST")
BACK_PORT = os.getenv("BACK_PORT")
SELF_HOST = "localhost"
SELF_PORT = os.getenv("SELF_PORT")

# TODO:  load instead of hardcoding
model = k.Sequential([
    k.Input(shape=(16,)),
    k.layers.Dense(9)
])

receive_ws = None
send_ws = None

# REFERENCE https://websockets.readthedocs.io/en/stable/


async def server(ws, path, forward_ws, back_ws, stop_ws):
    async for data in ws:
        read_buff = io.BytesIO()
        read_buff.write(data)
        read_buff.seek(0)
        write_buff = io.BytesIO()
        if path == "/forward":
            model_output = model(np.load(read_buff))
            np.save(write_buff,model_output)
            forward_ws.send(write_buff)
        elif path == "/backward":
            updates = np.load(read_buff)
            model.set_weights(updates[0]) # pop off update
            np.save(write_buff, updates[1:])
            back_ws.send(write_buff)
        elif path == "/stop":
            await stop_ws.send("")
            os.kill(os.getpid(), "SIGTERM")

async def main():
    connected = set()

    front_uri = f"ws://{FRONT_HOST}:{FRONT_PORT}"
    back_uri = f"ws://{BACK_HOST}:{BACK_PORT}"
    front_sender = websockets.connect(f"{front_uri}/forward")
    back_sender = websockets.connect(f"{back_uri}/backward")
    stop_sender = websockets.connect(f"{back_uri}/stop")
    connected.add(front_sender)
    connected.add(back_sender)
    connected.add(stop_sender)

    server_handler = functools.partial(server, front_ws = front_sender, back_ws = back_sender, stop_ws = stop_sender)
    loop = asyncio.get_event_loop()

    # Create server
    start_server = websockets.serve(server_handler, SELF_HOST, SELF_PORT)
    server_instance = loop.run_until_complete(start_server)

    # Run server until receiving SIGTERM signal
    stop = asyncio.Future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.run_until_complete(stop)
    
    # Shutdown server on stop
    server_instance.close()
    loop.run_until_complete(server.wait_closed())
   
    # Running indefinitely
    # async with websockets.serve(server_handler, SELF_HOST, SELF_PORT):
    #     
