from time import time
import numpy as np
from getpass import getuser
from glob import glob
from keras.models import Model, load_model
from typing import Dict, TypedDict, List
from json import dumps
from io import BytesIO
from os import stat, environ, path
import iperf3
from pythonping import ping
from getpass import getuser


def load_all_models() -> Dict[str, Model]:
    user_folder = glob(f"/home/*/")[0]
    model_paths = glob(f"{user_folder}models/*/")

    models: Dict[str, Model] = {}
    for model_path in model_paths:
        model = load_model(model_path)
        model_name = model_path.split("/")[-2]
        print(f"Loaded model: {model_path}")
        models[model_name] = model
    return models


class Config(TypedDict):
    model_test_number_of_repeats: int
    model_test_batch_size: int
    bandwidth_test_duration_sec: int
    latency_test_count: int


config: Config


def load_benchmark_configs():
    # TODO: read from environment variables
    global config
    config = Config(
        model_test_batch_size=1,
        model_test_number_of_repeats=1000,
        bandwidth_test_duration_sec=1,
        latency_test_count=1000)


def load_network_benchmark_ips() -> List[str]:
    return environ.get("PAPDL_WORKERS").split(" ")


def benchmark_time(model: Model) -> float:
    global config
    dimensions = (config["model_test_batch_size"],) + model.input_shape[1:]
    sample_input = np.random.random_sample(dimensions)

    start = time()
    [model(sample_input)
     for i in range(config["model_test_number_of_repeats"])]
    end = time()
    return (end - start) / config["model_test_number_of_repeats"]


def benchmark_size(model: Model) -> float:
    global config
    dimensions = (config["model_test_batch_size"],) + model.input_shape[1:]
    sample_input = np.random.random_sample(dimensions)

    output: np.array = model(sample_input, training=False)

    # buffer = BytesIO()
    # np.savez(buffer,x=output)
    np.save("fsize", output)
    size = stat("fsize.npy").st_size
    return size


def benchmark_model() -> Dict:
    print(f"Running as: {getuser()} ")
    global config
    models = load_all_models()
    load_benchmark_configs()
    results = {}
    for i, (name, model) in enumerate(models.items()):
        time = benchmark_time(model)
        size = benchmark_size(model)
        results[name] = {"benchmark_time": time, "benchmark_size": size}

    return results


def benchmark_network() -> Dict:
    # return load_network_benchmark_ips()
    global config
    result = {}
    for ip in load_network_benchmark_ips():

        # BANDWIDTH TEST
        client = iperf3.Client()
        client.duration = config["bandwidth_test_duration_sec"]
        client.server_hostname = ip
        client.port = 5201
        r_iperf: iperf3.TestResult = client.run()
        r_ping = ping(ip, count=config["latency_test_count"])

        result[ip] = {
            "bandwidth": {
                "sent_bps": r_iperf.sent_bps,
                "received_bps": r_iperf.received_bps
            },
            "latency": {
                "rtt_min_ms": r_ping.rtt_min_ms,
                "rtt_avg_ms": r_ping.rtt_avg_ms,
                "rtt_max_ms": r_ping.rtt_max_ms
            }
        }
        print(result[ip])
        del client
    return result


benchmark_result = {
    "model_performance": benchmark_model(),
    "network_performance": benchmark_network()
}

print("[BENCHMARK]" + dumps(benchmark_result))
