import os, asyncio, signal
from .wsc import Wsc
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '3'
from time import sleep
from .configure import ServerConfig

config = ServerConfig()

conns = {
    "forward_in" : Wsc("forward_in", "0.0.0.0", 8765, config.server_logger),
    "forward_out": Wsc("forward_out", config.FORWARD_URL, config.FOREWARD_PORT, config.server_logger)
}

async def forward(messages):
    async for data in messages:
        config.server_logger.info("Received...")
        input = Wsc.read_np(data)
        output = config.m.predict(input)
        while(not conns["forward_out"].connected):
            sleep(1)
        await conns["forward_out"].send(output)

#### SPAWN WEBSOCKET SERVER AND CLIENT
conns["forward_in"].serve(forward)
stop = asyncio.Future()
loop = asyncio.get_event_loop()
loop.run_until_complete(conns["forward_in"].conn)
loop.run_until_complete(conns["forward_out"].connect())
loop.add_signal_handler(signal.SIGTERM, stop.result, None)
loop.run_until_complete(stop)
