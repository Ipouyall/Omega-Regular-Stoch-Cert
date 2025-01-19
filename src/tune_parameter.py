import json
import os
from time import perf_counter

import numpy as np

from system.runner import Runner

def find_highest_possible_parameter(parameter_group, parameter_name, config_path, temp_path, upper_bound, precision, max_iterations=100):
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    temp_config_name = os.path.join(temp_path, "temp_config.json")
    temp_report_name = os.path.join(temp_path, "temp_report.txt")
    if os.path.exists(temp_report_name):
        os.remove(temp_report_name)
    def dump_config(config: dict):
        with open(temp_config_name, "w") as f:
            f.write(json.dumps(config, indent=4))
    def dump_report(report):
        with open(temp_report_name, "a") as f:
            f.write(report)
            f.write("\n")
    def is_satisfiable() -> bool:
        runner = Runner(temp_config_name, "")
        runner.run()
        return runner.history["solver_result"]["is_sat"] == "sat"

    with open(config_path, "r") as f:
        base_config = json.load(f)
    base_value = base_config[parameter_group][parameter_name]
    best_config = base_config
    dump_report(f'Start tuning for {parameter_name} in [{base_value}, {upper_bound}) with precision {precision}')
    precision = precision+1
    best_time = -1

    for _ in range(max_iterations):
        value_under_test = round((base_value + upper_bound)/2, precision)
        dump_report(f"TESTING for {parameter_name} = {value_under_test}")
        base_config[parameter_group][parameter_name] = value_under_test
        dump_config(base_config)
        start_time = perf_counter()
        is_sat = is_satisfiable()
        end_time = perf_counter()
        if is_sat:
            base_value = value_under_test
            best_config = base_config
            best_time = end_time - start_time
            dump_report(f"Found satisfiable solution for {parameter_name} = {value_under_test}")
            dump_report(f"NEW BEST VALUE for {parameter_name}: {base_value}")
            dump_report(f"TIME: {best_time:3f} seconds")
        else:
            dump_report(f"Failed to find satisfiable solution for {parameter_name} = {value_under_test}")
            upper_bound = value_under_test
        if upper_bound - base_value < 10**-precision:
            dump_report(f"Reached precision limit for {parameter_name}")
            break
    dump_report(f"Final best value for {parameter_name}: {base_value}")
    dump_report(f"TIME: {best_time:.3f} seconds")
    dump_config(best_config)
    return base_value, best_time

def benchmark_runner(path, iterations=10):
    runtimes = []
    for _ in range(iterations):
        start_time = perf_counter()
        runner_instance = Runner(path, "")
        runner_instance.run()
        end_time = perf_counter()
        assert runner_instance.history["solver_result"]["is_sat"] == "sat", "Failed to satisfy the constraints"

        runtimes.append(end_time - start_time)
    mean_runtime = np.mean(runtimes)
    std_runtime = np.std(runtimes)

    print(f"Mean Runtime: {mean_runtime:.9f} seconds")
    print(f"Standard Deviation of Runtime: {std_runtime:.9f} seconds")
    print(f"Mean Runtime: {mean_runtime:.3f} ± {std_runtime:.3f} seconds")

    return mean_runtime, std_runtime


if __name__ == "__main__":
    config_file = "./benchmark/random_walk_control_1.json"

    v = find_highest_possible_parameter(
        parameter_group="synthesis_config",
        parameter_name="probability_threshold",
        config_path=config_file,
        temp_path="./benchmark/tuning",
        upper_bound=1,
        precision=5,
        max_iterations=100
    )
    print(f"\nFinal best value for probability_threshold {v[0]} in {v[1]:.3f} seconds")

    # benchmark_runner(config_file, iterations=1)
