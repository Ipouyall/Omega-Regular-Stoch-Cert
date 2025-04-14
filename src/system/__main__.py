import argparse
import os

from . import benchmark_runner, dump_results_to_table, bulk_benchmark_runner, dump_log_result, convert_results_to_table

parser = argparse.ArgumentParser(description="The implementation of the 'Supermartingale Certificates for Quantitative Omega-regular Verification and Control' paper.")
parser.add_argument("--input", type=str, nargs="?", default=None, help="Path to the input file for the system. This can be a single file or a directory (default: None)")
parser.add_argument("--iterations", type=int, default=1, help="Number of iterations to run the system (default: 1)")
parser.add_argument("--output", type=str, nargs="?", default="benchmark_results.txt", help="Path to the file you want to dump the results to (default: benchmark_results.txt)")
parser.add_argument("--dump-log", action="store_true", help="Dump the log of the system to a file (default: False)")
parser.add_argument("--visualize", action="store_true", help="Visualize the results of the system (default: False)")
args = parser.parse_args()

# print(f"Running the system with the following arguments:")
# for arg, value in vars(args).items():
#     print(f"{arg:<11}>> {value}")

if not args.input:
    raise ValueError("Please provide a path to the input file for the system")

if args.visualize:
    convert_results_to_table(dump_file=args.input, output_file=args.output)
elif os.path.isdir(args.input):
    print("Running the system in bulk mode")
    table_data = bulk_benchmark_runner(args.input)
    dump_results_to_table(table_data)
elif os.path.isfile(args.input):
    mean, std, stat, prob, spec = benchmark_runner(path=args.input, iterations=args.iterations, report_mode=True)
    if args.dump_log:
        data = {
            "Experiment": os.path.basename(args.input),
            "Specification": spec,
            "Probability": prob,
            "Runtime": mean,
            "Status": "Succeeded" if stat else "Failed"
        }
        dump_log_result(data, output_file=args.output)
else:
    raise ValueError(f"Invalid path provided for the system: {args.input}")


