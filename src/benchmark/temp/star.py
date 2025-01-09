import os.path
import numpy as np
from polyhorn.main import execute
from time import perf_counter

def benchmark_runner(path, iterations=10):
    runtimes = []
    input_file = os.path.join(path, "temporary_polyhorn_input.smt2")
    config_file = os.path.join(path, "temporary_polyhorn_config.json")
    for _ in range(iterations):
        start_time = perf_counter()
        is_sat, model = execute(input_file, config_file)
        end_time = perf_counter()
        assert is_sat == "sat", "Failed to satisfy the constraints"
        runtimes.append(end_time - start_time)

    mean_runtime = np.mean(runtimes)
    std_runtime = np.std(runtimes)

    report = f"Mean Runtime: {mean_runtime:.3f} ± {std_runtime:.3f} seconds"
    print(report)

    return report


if __name__ == "__main__":
    base = "./"
    report_file = "./cumulative_report.txt"
    benchmarks = [
        d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))
    ]
    with open(report_file, "w") as f:
        for benchmark in benchmarks:
            print(f"Running benchmark: {benchmark}")
            path = os.path.join(base, benchmark)
            report = benchmark_runner(path, iterations=10)
            f.write(f"{benchmark}: {report}\n")
            f.flush()
            print(f"Finished benchmark: {benchmark}")
