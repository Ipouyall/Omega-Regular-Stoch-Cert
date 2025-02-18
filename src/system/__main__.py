"""
you can run this module in following format:
python -m system file_path iterations
"""
import argparse
import os

from . import benchmark_runner, dump_results_to_table

parser = argparse.ArgumentParser(description="The implementation of the 'Supermartingale Certificates for Quantitative Omega-regular Verification and Control' paper.")
parser.add_argument("--file", type=str, nargs="?", default=None, help="Path to the input file for the system")
parser.add_argument("--iterations", type=int, default=1, help="Number of iterations to run the system (default: 1)")
parser.add_argument("--output", type=str, nargs="?", default="benchmark_results.txt", help="Path to the file you want to dump the results to (default: benchmark_results.txt)")
args = parser.parse_args()

# print(f"Running the system with the following arguments:")
# for arg, value in vars(args).items():
#     print(f"{arg:<11}>> {value}")

if not args.file:
    raise ValueError("Please provide a path to the input file for the system")

# check if the file is a directory
if os.path.isdir(args.file):
    print("Running the system in bulk mode")
    dump_results_to_table(args.file)
elif os.path.isfile(args.file):
    mean_runtime, std_runtime = benchmark_runner(path=args.file, iterations=args.iterations)
else:
    raise ValueError(f"Invalid path provided for the system: {args.file}")


