import signal
import asyncio
from .wsc import Wsc
from .configure import ServerConfig
from time import sleep
import numpy as np
import os
import functools
import io
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'


config = ServerConfig()


conns = {
    "forward_in": Wsc("forward_in", "0.0.0.0", 8765, config.server_logger),
    "forward_out": Wsc("forward_out", config.FORWARD_URL, config.FOREWARD_PORT, config.server_logger)
}


async def forward(messages):
    async for data in messages:
        result = Wsc.read_np(data)
        config.server_logger.info(f"Received output: {result}")


async def send_random_data():
    sleep(10)
    for i in range(100):
        sample = np.random.random((1, 100))
        config.server_logger.info(f"Sending input...")
        while (not conns["forward_out"].connected):
            config.server_logger.info("Sleeping forward orchestrator")
            sleep(1)
        await conns["forward_out"].send(sample)


# SPAWN WEBSOCKET SERVER AND CLIENT
conns["forward_in"].serve(forward)
stop = asyncio.Future()
loop = asyncio.get_event_loop()
loop.run_until_complete(conns["forward_in"].conn)
loop.run_until_complete(conns["forward_out"].connect())
loop.run_until_complete(send_random_data())

loop.add_signal_handler(signal.SIGTERM, stop.result, None)
loop.run_until_complete(stop)
