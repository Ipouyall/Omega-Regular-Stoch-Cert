
# Instruction.md

## Overview

This document provides complete and professional instructions for installing, running, and reproducing the experiments associated with our paper:

**Title**: *Supermartingale Certificates for Quantitative Omega-regular Verification and Control*  
**Authors**: **[TO BE FILLED]**  
**DOI**: *[TO BE FILLED]*  
**Artifact SHA256**: *[TO BE FILLED]*  

This artifact supports full reproducibility of the paper's results and facilitates experimentation with user-defined benchmarks.

---

## 1. Artifact Check-list

- **Operating System**: macOS 15.3.2 (tested); cross-platform via Docker
- **Installation**: `requirements.txt` (native) or prebuilt Docker image
- **Dependencies**: Python 3.12, `z3-solver`, PolyQEnt (formerly PolyHorn)
- **Hardware Requirements**: No special hardware required; tested on systems with 16GB RAM
- **Expected Runtime**: Each benchmark runs in seconds to a few minutes
- **License**: MIT
- **Artifact Availability**: Yes, hosted on GitHub / Zenodo (see DOI)
- **Reusability**: Out tool supports for custom benchmarks. Please refer to [**Designing Custom Benchmark**](#5-designing-custom-benchmarks).
- **Functionality**: Fully functional as described in the paper. Please refer to [**Reproducing Paper Results**](#4-reproducing-paper-results).

---

## 2. Setup Instructions

### Docker

1. **Load the image:** You can use the provided Docker image. To load the provided prebuilt image, use command below:

   ```bash
   docker load -i system.tar
   ```

2. **To run the container:** After loading the image, you can run the container using:

   ```bash
   docker run -it system:v0.1
   ```

> If you need more details on Docker usage, please refer to [`Documents/docker.md`](./docker.md).

---

## 3. Running the Artifact

This tool operates on benchmarks defined as JSON files, described in detail in [`Documents/input_format.md`](./input_format.md). Each execution generates a report that includes:

- Benchmark success/failure
- Synthesized certificate
- Runtime metrics
- Benchmark summary

> For guidance on interpreting results, see [`Documents/output_format.md`](./output_format.md).

### CLI Usage

Run a single benchmark:

```bash
python3 -m system --input <path_to_benchmark.json>
```

Run all benchmarks in a directory:

```bash
python3 -m system --input ./benchmark [--output <output_file>]
```

### Python API Usage

Use `runner_check.py` to run a benchmark programmatically:

```python
from system import benchmark_runner

if __name__ == "__main__":
    config_file = "./benchmark/random_walk_verification_3.json"
    benchmark_runner(config_file, iterations=1)
```

---

## 4. Reproducing Paper Results

To reproduce all experimental results from the paper:
1. Install the system or run the docker image, as described in [**Setup Instructions**](#2-setup-instructions).
2. Run the benchmarks using the command below:
   
   ```bash
   python3 -m system --input ./benchmark
   ```

This command runs all benchmarks in the `./benchmark` directory. Outputs, including the summarized result table, are saved to `benchmark_results.txt` and is printed in the terminal after running each benchmark.

---

## 5. Designing Custom Benchmarks

### Input Format

Custom benchmarks should conform to the format documented in [`Documents/input_format.md`](./input_format.md). 
Each file specifies the stochastic system dynamics, properties, and objective.

### Output Format

Output files include:

- Success/failure of the benchmark
- Synthesized certificate
- Runtime metrics
- Summary of the benchmark and its properties

See [`Documents/output_format.md`](./output_format.md) for a detailed breakdown.

---

## 6. Docker Usage

Comprehensive Docker instructions are provided in [`Documents/docker.md`](./docker.md), covering:

- Building the Docker image
- Running with volume mounts
- Saving/loading containers

Docker ensures full environment reproducibility for artifact evaluation.

---

## 7. License

This artifact is distributed under the **MIT License**, allowing open use, modification, and distribution with appropriate attribution.

---
