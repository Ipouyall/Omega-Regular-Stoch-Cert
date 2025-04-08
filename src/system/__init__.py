from time import perf_counter
import numpy as np
from tabulate import tabulate
import os

from .runner import Runner


def dump_results_to_table(table_data, output_file="benchmark_results.txt"):
    table = tabulate(table_data, headers="keys", tablefmt="grid")
    print(table)

    if output_file is None:
        return
    with open(output_file, "w") as f:
        f.write(table)
    print(f"Results saved to {output_file}")


def benchmark_runner(path, iterations=1, report_mode=False):
    runtimes = []
    stat = True if iterations >= 1 else None
    prob = None
    spec = None  # TODO: Processor to add lookup table as well
    succeeded = lambda x: x.history["solver_result"]["is_sat"] == "sat"

    for _ in range(iterations):
        start_time = perf_counter()
        runner_instance = Runner(path, "")
        runner_instance.run()
        end_time = perf_counter()
        print(f"Runtime: {end_time - start_time:.3f} seconds")
        if not report_mode:
            assert succeeded(runner_instance), "Failed to satisfy the constraints"
        runtimes.append(end_time - start_time)
        stat = stat and succeeded(runner_instance)
        prob = runner_instance.history["synthesis"].probability_threshold
        spec = runner_instance.history["initiator"].specification_pre["ltl_formula"]

    mean_runtime = np.mean(runtimes)
    std_runtime = np.std(runtimes)

    print(f"Mean Runtime: {mean_runtime:.9f} seconds")
    print(f"Standard Deviation of Runtime: {std_runtime:.9f} seconds")
    print(f"Runtime: {mean_runtime:.3f} ± {std_runtime:.3f} seconds")

    if report_mode:
        return mean_runtime, std_runtime, stat, prob, spec
    return mean_runtime, std_runtime


def bulk_benchmark_runner(dir_path):
    dir_files = os.listdir(dir_path)
    dir_files = [file for file in dir_files if file.endswith(".yml") or file.endswith(".yaml") or file.endswith(".json")]
    dir_files.sort()

    report = {
        "Experiment": [],
        "Specification": [],
        "Probability": [],
        "Runtime": [],
        "Status": [],
    }

    for file in dir_files:
        print(f"Running benchmark for {file}")
        report["Experiment"].append(file)
        try:
            mean_runtime, std_runtime, stat, prob, spec = benchmark_runner(
                path=os.path.join(dir_path, file),
                iterations=1,
                report_mode=True
            )
            report["Runtime"].append(mean_runtime)
            report["Status"].append("Succeeded" if stat else "Failed")
            report["Probability"].append(prob)
            report["Specification"].append(spec)
        except Exception as e:
            print(f"Failed to run the experiment: {e}")
            report["Runtime"].append("Unknown")
            report["Status"].append("Error")
            report["Probability"].append("Unknown")
            report["Specification"].append("Unknown")

        dump_results_to_table(report, output_file=None)
    print("Benchmarking completed")
    return report



