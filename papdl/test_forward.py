import numpy as np
import keras as k
import asyncio
import websockets
import io

test_forwarder = np.random.random((1,1600))

write_buff = io.BytesIO()
np.save(write_buff,test_forwarder,allow_pickle=True)
write_buff.seek(0)

print("INPUT:")
print(test_forwarder)

async def hello():
    async with websockets.connect("ws://127.0.0.1:8765") as ws:
        await ws.send(write_buff)
        result = await ws.recv()
        read_buff = io.BytesIO()
        read_buff.write(result)
        read_buff.seek(0)
        print("OUTPUT:")
        print(np.load(read_buff))

asyncio.get_event_loop().run_until_complete(hello())