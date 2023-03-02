import logging
import os
import keras as k
import getpass


class ServerConfig:
    def __init__(self):
        self.server_logger = logging.getLogger("server")
        server_logger_handler: logging.StreamHandler = logging.StreamHandler()
        server_logger_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(name)-6s] %(levelname)-8s %(message)s"
                              ))
        self.server_logger.addHandler(server_logger_handler)
        self.server_logger.setLevel(logging.DEBUG)

        self.FORWARD_URL = os.getenv("FORWARD_URL")
        self.FOREWARD_PORT = 8765

        self.m = k.models.load_model(f"/home/{getpass.getuser()}/model")
        self.m.compile()
