# Supermartingale Certificates for Quantitative Omega-regular Verification and Control

This repository contains the source code for the paper "Supermartingale Certificates for Quantitative Omega-regular Verification and Control", the benchmarks used in the paper, and instructions on how to use the code.

---

## Requirements

We used `python 3.12.5` for our experiments. After installing python, you can install the required packages using the following command:

```bash
pip install -r requirements.txt
```

Or manually install these packages:

- `pip install lark==1.2.2`
- `pip install polyhorn==0.0.7`
- `pip install sympy==1.13.2`
- `pip install matplotlib==3.9.2`
- `pip install numpy==2.1.1`
- `pip install pandas==2.2.3`

Ypu also need to install SMT-solvers so that the code can use them. To install Z3, you can use the following command:

```bash
pip install z3-solver
```

- For more information on how to install Z3, you can visit the [Z3 GitHub page](https://github.com/Z3Prover/z3).
- To download the MathSAT, you can visit the [MathSat website](https://mathsat.fbk.eu/download.html).
- Also for more information on PolyQEnt, you can visit the [PolyQEnt GitHub page](https://github.com/ChatterjeeGroup-ISTA/polyqent).

## Execution

To execute a benchmark, You have two options:
1. Using a python script
2. Using the command line
3. Using the provided Docker image (this option supports both methods above)

### Run the benchmarks using a python script

To run the benchmarks using a python script, you can use the `runner_check.py` script. 
To run different benchmarks, you just need to modify _config_file_ in the script.

```python
from system import benchmark_runner

if __name__ == "__main__":
    config_file = "./benchmark/random_walk_verification_3.json"

    benchmark_runner(config_file, iterations=1)
```

### Run the benchmarks using the command line

To run the benchmarks using the command line, you can use the following command:

```bash
python3 -m system --file <path_to_your_benchmark> [--iterations <number_of_iterations>]
```


