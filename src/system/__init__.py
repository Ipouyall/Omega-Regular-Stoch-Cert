from time import perf_counter
import numpy as np
from tabulate import tabulate
import os

from .runner import Runner


def benchmark_runner(path, iterations=1, safe_mode=False):
    runtimes = []
    stats = []
    succeeded = lambda x: x.history["solver_result"]["is_sat"] == "sat"
    for _ in range(iterations):
        start_time = perf_counter()
        runner_instance = Runner(path, "")
        runner_instance.run()
        end_time = perf_counter()
        print(f"Runtime: {end_time - start_time:.3f} seconds")
        if not safe_mode:
            assert succeeded(runner_instance), "Failed to satisfy the constraints"
        runtimes.append(end_time - start_time)
        stats.append(succeeded(runner_instance))
    mean_runtime = np.mean(runtimes)
    std_runtime = np.std(runtimes)

    print(f"Mean Runtime: {mean_runtime:.9f} seconds")
    print(f"Standard Deviation of Runtime: {std_runtime:.9f} seconds")
    print(f"Mean Runtime: {mean_runtime:.3f} ± {std_runtime:.3f} seconds")

    if safe_mode:
        return mean_runtime, std_runtime, stats
    return mean_runtime, std_runtime


def bulk_benchmark_runner(dir_path):
    dir_files = os.listdir(dir_path)
    dir_files = [file for file in dir_files if file.endswith(".yml") or file.endswith(".yaml") or file.endswith(".json")]

    experiments = []
    run_time = []
    status = []

    for file in dir_files:
        print(f"Running benchmark for {file}")
        experiments.append(file)
        try:
            mean_runtime, std_runtime, stat = benchmark_runner(os.path.join(dir_path, file), iterations=1, safe_mode=True)
            run_time.append(mean_runtime)
            status.append("Succeeded" if all(stat) else "Failed")
        except Exception as e:
            print(f"Failed to run the experiment: {e}")
            run_time.append("Unknown")
            status.append("Failed")
    return experiments, run_time, status


def dump_results_to_table(dir_path, output_file="benchmark_results.txt"):
    experiments, run_time, status = bulk_benchmark_runner(dir_path)

    table_data = zip(experiments, run_time, status)
    table = tabulate(table_data, headers=["Experiment", "Runtime", "Status"], tablefmt="grid")

    with open(output_file, "w") as f:
        f.write(table)

    print(f"Results saved to {output_file}")
    print(table)

