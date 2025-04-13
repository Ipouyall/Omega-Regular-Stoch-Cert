# Instruction.md

## Overview

This document provides complete and professional instructions for installing, running, and reproducing the experiments associated with our paper artifact.  
It is prepared specifically for the **artifact evaluation** of our submission to CAV 2025.

**Title**: *Supermartingale Certificates for Quantitative Omega-regular Verification and Control*  
**Authors**: **[TO BE FILLED]**  
**DOI**: *[TO BE FILLED]*  
**Artifact SHA256**: *[TO BE FILLED]*  

This artifact supports full reproducibility of the results presented in the paper and facilitates experimentation with user-defined benchmarks.

---

## Table of Contents

1. [Artifact Check-list](#1-artifact-check-list)  
2. [Setup Instructions](#2-setup-instructions)  
3. [Running the Artifact](#3-running-the-artifact)  
4. [Reproducing Paper Results](#4-reproducing-paper-results)  
5. [Designing Custom Benchmarks](#5-designing-custom-benchmarks)  
6. [Docker Usage](#6-docker-usage)  
7. [License](#7-license)  

---

## 1. Artifact Check-list

- **Operating System**: macOS 15.3.2 (tested); cross-platform via Docker
- **Installation**: `requirements.txt` (native) or prebuilt Docker image
- **Dependencies**: Python 3.12, `z3-solver`, PolyQEnt (formerly PolyHorn)
- **Hardware Requirements**: No special hardware required; tested on systems with 16GB RAM
- **Expected Runtime**: Each benchmark runs in seconds to a few minutes
- **License**: MIT
- **Artifact Availability**: Yes, hosted on GitHub / Zenodo (see DOI)
- **Reusability**: Our tool supports custom benchmarks. Please refer to [**Designing Custom Benchmarks**](#5-designing-custom-benchmarks).
- **Functionality**: Fully functional as described in the paper. Please refer to [**Reproducing Paper Results**](#4-reproducing-paper-results).

---

## 2. Setup Instructions

### Docker

1. **Load the image**: Use the provided Docker image. To load the prebuilt image, run:

   ```bash
   gunzip -c system.tar.gz | docker load
   ```

2. **Run the container**: After loading, start the container with:

   ```bash
   docker run -it system:v0.1
   ```

> For more details on Docker usage, refer to [`Documents/docker.md`](./docker.md).

---

## 3. Running the Artifact

This tool operates on benchmarks defined in JSON format, as described in [`Documents/input_format.md`](./input_format.md).  
Each run generates a report including:

- Success/failure of the benchmark
- Synthesized certificate
- Runtime metrics
- Benchmark summary

> For output interpretation, refer to [`Documents/output_format.md`](./output_format.md).  

> For designing your own benchmarks, refer to [`Documents/input_format.md`](./input_format.md).

### CLI Usage

Run a single benchmark:

```bash
python3 -m system --input <path_to_benchmark.json>
```

Run all benchmarks in a directory:

```bash
python3 -m system --input ./benchmark [--output <output_file>]
```

This command processes all benchmarks in the `./benchmark` directory, 
starting with verification problems followed by control problems.  
Results are saved in `benchmark_results.txt` (or as specified with `--output`) and printed to the terminal.

### Python API Usage

To run benchmarks programmatically, use `runner_check.py`:

```python
from system import benchmark_runner

if __name__ == "__main__":
    config_file = "./benchmark/random_walk_verification_0.json"  # Path to your benchmark file
    benchmark_runner(config_file, iterations=1)
```

---

## 4. Reproducing Paper Results

To reproduce all experiments from the paper:

1. Install the system or load the Docker image as outlined in [**Setup Instructions**](#2-setup-instructions).
2. Run:

   ```bash
   python3 -m system --input ./benchmark
   ```

This command runs all benchmarks in the `./benchmark` directory.  
Results, including the summary table, are saved to `benchmark_results.txt` and printed to the terminal.

---

## 5. Designing Custom Benchmarks

### Input Format

Custom benchmarks should follow the format described in [`Documents/input_format.md`](./input_format.md).  
Each file defines stochastic system dynamics, target properties, and analysis objectives.

### Output Format

Output files include:

- Success/failure of the benchmark
- Synthesized certificate
- Runtime metrics
- Benchmark and property summary

For full details, refer to [`Documents/output_format.md`](./output_format.md).

---

## 6. Docker Usage

For comprehensive Docker usage, consult [`Documents/docker.md`](./docker.md), which includes:

- Building the Docker image
- Running with volume mounts
- Saving and loading containers

Docker guarantees full environment reproducibility and simplifies artifact evaluation.

---

## 7. License

This artifact is released under the **MIT License**, permitting open use, modification, and distribution with proper attribution.

---
