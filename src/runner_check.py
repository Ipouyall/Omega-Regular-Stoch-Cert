from system import benchmark_runner

if __name__ == "__main__":
    config_file = "./benchmark/random_walk_verification_3.json"

    benchmark_runner(config_file, iterations=1)
