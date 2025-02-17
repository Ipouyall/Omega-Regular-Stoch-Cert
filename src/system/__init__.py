from time import perf_counter
import numpy as np

from .runner import Runner


def benchmark_runner(path, iterations=1):
    runtimes = []
    for _ in range(iterations):
        start_time = perf_counter()
        runner_instance = Runner(path, "")
        runner_instance.run()
        end_time = perf_counter()
        print(f"Runtime: {end_time - start_time:.3f} seconds")
        assert runner_instance.history["solver_result"]["is_sat"] == "sat", "Failed to satisfy the constraints"

        runtimes.append(end_time - start_time)
    mean_runtime = np.mean(runtimes)
    std_runtime = np.std(runtimes)

    print(f"Mean Runtime: {mean_runtime:.9f} seconds")
    print(f"Standard Deviation of Runtime: {std_runtime:.9f} seconds")
    print(f"Mean Runtime: {mean_runtime:.3f} ± {std_runtime:.3f} seconds")

    return mean_runtime, std_runtime
