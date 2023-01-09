from configure import ServerConfig
from time import time
import numpy as np

config = ServerConfig()
## Benchmark parameters
number_of_repeats = 10
batch_size = 10

result = []
for i in range(number_of_repeats):
   dimensions = (batch_size,) + config.m.input_shape[1:]
   sample_input = np.random.random_sample(dimensions)
   start = time() 
   config.m.predict(sample_input)
   end = time()
   duration = end - start
   result.append(str(duration))

print("[BENCHMARK]" + ",".join(result))
   