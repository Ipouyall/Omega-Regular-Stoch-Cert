"""
you can run this module in following format:
python -m system file_path iterations
"""
import argparse

from . import benchmark_runner

parser = argparse.ArgumentParser(description="The implementation of the 'Supermartingale Certificates for Quantitative Omega-regular Verification and Control' paper.")
parser.add_argument("--file", type=str, nargs="?", default=None, help="Path to the input file for the system")
parser.add_argument("--iterations", type=int, default=1, help="Number of iterations to run the system (default: 1)")

args = parser.parse_args()

print(f"Running the system with the following arguments:")
for arg, value in vars(args).items():
    print(f"{arg:<10}>> {value}")

mean_runtime, std_runtime = benchmark_runner(path=args.file, iterations=args.iterations)


