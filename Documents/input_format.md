# System's input format

The input file consists of five subsections:

1. **[Stochastic Dynamical System](#stochastic-dynamical-system)**
2. **[Actions](#actions)**
3. **[Disturbance](#disturbance)**
4. **[Specification](#specification)**
5. **[Synthesis Config](#synthesis-config)**

You can organize these sections in two ways:
- **Single File:** Define all sections in one file.
- **Multiple Files:** Split sections across multiple files.

The system supports both **JSON** and **YAML** formats.

> [!TIP]
> For the **Multi-Files** mode, do not split each subsection into multiple files.

> [!IMPORTANT]
> The system assumes inputs are valid and may not check for all errors before execution.

Next, we provide examples and detailed descriptions for each section. At the end of this file, we would have two sections:
- [Single file example](#single-file-example) which provides an example of how an input file should look like.
- [Additional Formatting Guidelines](#additional-formatting-guidelines) which provides a standardized format for defining predicates and equations that used throughout the system. This also discuss the troubleshooting steps for some errors.

## Stochastic Dynamical System

This section defines the system schema, including its dynamics, dimensions, constraints, and transformations.

### Example Format
```json
{
  "stochastic_dynamical_system": {
    "state_space_dimension": 1,
    "control_space_dimension": 0,
    "disturbance_space_dimension": 1,
    "system_space": "S1 <= 150",
    "initial_space": "2 <= S1 <= 3",
    "dynamics": [
      {
        "condition": "S1 <= 100",
        "transforms": [
          "S1 + D1"
        ]
      },
      {
        "condition": "S1 >= 100",
        "transforms": [
          "S1"
        ]
      }
    ]
  }
}
```

### Parameter Descriptions
- **state_space_dimension**: Number of state variables or the dimension of the system.
- **control_space_dimension**: Number of control variables (`π: Dim(StateSpace) -> Dim(ControlSpace)`).
- **disturbance_space_dimension**: Number of disturbance variables.
- **system_space**: Constraints on state variables, which defines the system boundaries. The constraints should be defined as inequalities in the state variables. Read more about the format at [Space Format](#space-format).
- **initial_space**: Constraints on state variables, which define the initial state of the system. The constraints should be defined as inequalities in the state variables. Read more about the format at [Space Format](#space-format).
- **dynamics**: List of piecewise polynomial transformations, each defined by:
  - **condition**: Predicate defining when the transformation applies. Read more about the format at [Space Format](#space-format).
  - **transforms**: List of polynomials representing system evolution.

### Variable Specification
#### State Variables
For an _n_-dimensional system:

$$
\mathbf{S} = \begin{bmatrix} S_1 & S_2 & \dots & S_n \end{bmatrix}
$$

For example, `S1` refers to the first state variable, `S2` to the second, etc.

#### Action Variables
For an _m_-dimensional control space:

$$
\mathbf{A} = \begin{bmatrix} A_1 & A_2 & \dots & A_m \end{bmatrix}
$$

#### Disturbance Variables
For a _k_-dimensional disturbance space:

$$
\mathbf{D} = \begin{bmatrix} D_1 & D_2 & \dots & D_k \end{bmatrix}
$$

### Defining System Dynamics
#### Conditions
Conditions must be predicates on state variables. Here are some examples for a 2D system:
- **Valid Conditions:**
  - `S1 <= 100`
  - `S1 + S2 <= 100`
  - `S1**2 + S2**2 <= 100` (Defines a circle)
  - `-2 <= S1 <= 2 and -2 <= S2 <= 2` (Defines a square)

- **Invalid Conditions:**
  - `S3 <= 100` (Variable `S3` does not exist in a 2D system)
  - `S1 <= 10 or S2 <= 10` (Only conjunctions are allowed)
  - `S1 + S2 <= 2*S1 + S2**2` (Variables cannot appear on both sides)

Please refer to the [Space Format](#space-format) section for more information.

> [!TIP]
> If only one transformation exists, use a universally true condition, e.g., `0 <= 1`.

#### Transformations
Each transformation equation must be a polynomial in **state, action, and disturbance** variables. For a 3-state system:
```json
{
  "transforms": [
    "T1",
    "T2",
    "T3"
  ]
}
```
Where:

$$
S'_1 = T1(S,A,D) \quad S'_2 = T2(S,A,D) \quad S'_3 = T3(S,A,D)
$$

---

## Actions

### Example Format
```json
{
  "actions": {
    "maximal_polynomial_degree": 3,
    "control_policy": [],
    "minimum": -2,
    "maximum": 2
  }
}
```

- **maximal_polynomial_degree**: Maximum polynomial degree for the control policy.
- **control_policy**: List of polynomials representing the control policy.
- **minimum**: Minimum value for control variables. This is an optional field and if not provided, no minimum value is enforced.
- **maximum**: Maximum value for control variables. This is an optional field and if not provided, no maximum value is enforced.

The system supports three modes:
- **[Verification](#system-verification)**
- **[Control](#controller-synthesis)**

### System Verification
In this mode, the system has no actions. You should set `stoachastic_dynamical_system.constrol_space_dimension` $= 0$.


### Controller Synthesis
For Controller (or policy) synthesis, the condition is to set `stochastic_dynamical_system.constrol_space_dimension` $\neq0$. You should also set `control_policy` as an empty list, so the system would synthesize the policy template. You may provide any of the $[minimum, maximum]$ values to enforce bounds on the control variables.
```json
{
  "actions": {
    "maximal_polynomial_degree": 2,
    "control_policy": [],
    "minimum": -2,
    "maximum": 2
  }
}
```

> [!TIP]
> If `maximal_polynomial_degree` is omitted, the system will use the value from **[Synthesis Config](#synthesis-config)**.

> [!NOTE]
> Since the whole action section is optional, you may omit this section and just mentioning the `constrol_space_dimension` in the `stochastic_dynamical_system` section, which would be $\neq0$ for policy synthesis.

---

## Disturbance

### Example Format
```json
{
  "disturbance": {
    "distribution_name": "normal",
    "disturbance_parameters": {
      "mean": [0],
      "std": [1]
    }
  }
}
```

- **distribution_name**: Must be `normal` or `uniform`.
- **disturbance_parameters**: Define distribution properties.

> [!IMPORTANT]
> The current implementation only supports **one-dimensional** disturbances.

### Distribution Parameters

In the current version of the system, only `normal` and `uniform` distributions are supported. The parameters for each distribution are as follows:
- **Normal Distribution** ($\mathcal{N}(\mu, \sigma)$):
  - **mean** ($\mu$): Mean of the distribution.
  - **std** ($\sigma$): Standard deviation of the distribution.
- **Uniform Distribution** ($\mathcal{U}(a, b)$):
  - **lower_bound** ($a$): Lower bound of the distribution.
  - **upper_bound** ($b$): Upper bound of the distribution.

---

## Specification

### Example Format
```json
{
  "specification": {
    "ltl_formula": "(G F a) -> (G F b)",
    "proposition_lookup": {
      "a": "S1 > 0", 
      "b": "S2 > 0"
    }
  }
}
```
- **ltl_formula**: LTL formula.
- **preposition_lookup**: Maps atomic propositions to state constraints. This is optional. Read more about the format at [Space Format](#space-format).

Alternatively, an **HOA file** can be used:
```json
{
  "specification": {
    "hoa_path": "<path-to-hoa-file>"
  }
}
```

> [!NOTE]
> If using `preposition_lookup`, atomic propositions must be lowercase letters (`a-z`).

---

## Synthesis Config

### Example Format
```json
{
  "synthesis_config": {
    "use_linear_invariant": false,
    "maximal_polynomial_degree": 1,
    "probability_threshold": 0.99,
    "theorem_name": "farkas",
    "solver_name": "z3",
    "owl_path": "<path-to-owl-binary>"
  }
}
```

- **use_linear_invariant**: Whether to use a linear invariant.
- **maximal_polynomial_degree**: Maximum polynomial degree for templates and policies.
- **probability_threshold**: Probability threshold.
- **theorem_name**: Can be `farkas`, `handelman`, or `putinar`.
- **solver_name**: Can be `z3` or `mathsat`.
- **owl_path**: Path to OWL binary.

> [!TIP]
> If `hoa_path` is specified here, the system will use the HOA file instead of generating an automaton.

## Single file example

### System Verification

```json
{
  "actions": {
    "maximal_polynomial_degree": 1,
    "control_policy": []
  },

  "disturbance": {
    "distribution_name": "uniform",
    "disturbance_parameters": {
      "lower_bound": [-2],
      "upper_bound": [1]
    }
  },

  "stochastic_dynamical_system": {
    "state_space_dimension": 1,
    "control_space_dimension": 0,
    "disturbance_space_dimension": 1,
    "system_space": "S1 <= 150",
    "initial_space": "2 <= S1 <= 3",
    "dynamics": [
      {
        "condition": "S1 <= 100",
        "transforms": [
          "S1 + D1"
        ]
      },
      {
        "condition": "S1 >= 100",
        "transforms": [
          "S1"
        ]
      }
    ]
  },

  "synthesis_config": {
    "use_linear_invariant": true,
    "maximal_polynomial_degree": 1,
    "probability_threshold": 0.9999,
    "theorem_name": "farkas",
    "solver_name": "z3",
    "owl_path": "<path to owl binary>"
  },

  "specification": {
    "ltl_formula": "GF a",
    "proposition_lookup": {
      "a": "S1 <= 0"
    }
  }
}
```

### Policy Synthesis

```json
{
  "actions": {
    "maximal_polynomial_degree": 1,
    "control_policy": [],
    "minimum": -2,
    "maximum": 2
  },

  "disturbance": {
    "distribution_name": "uniform",
    "disturbance_parameters": {
      "lower_bound": [0],
      "upper_bound": [2]
    }
  },

  "stochastic_dynamical_system": {
    "state_space_dimension": 1,
    "control_space_dimension": 1,
    "disturbance_space_dimension": 1,
    "system_space": "S1 <= 150",
    "initial_space": "2 <= S1 <= 3",
    "dynamics": [
      {
        "condition": "S1 <= 100",
        "transforms": [
          "S1 + D1 + A1"
        ]
      },
      {
        "condition": "100 <= S1",
        "transforms": [
          "S1"
        ]
      }
    ]
  },

  "synthesis_config": {
    "use_linear_invariant": true,
    "maximal_polynomial_degree": 1,
    "probability_threshold": 0.9999,
    "theorem_name": "farkas",
    "solver_name": "z3",
    "owl_path": "<path to owl binary>"
  },

  "specification": {
    "ltl_formula": "(GF a)",
    "proposition_lookup": {
      "a": "S1 <= -2"
    }
  }
}
```

## Additional Formatting Guidelines

This section provides a standardized format for defining predicates used throughout the system. This also discuss the troubleshooting steps for some errors.

### Space Format

In our system, we use a specific structure, referred to as **space format**, to define predicates. This format ensures consistency in specifying constraints and conditions within the system.
First, we define this format, followed by examples of valid and invalid predicates for a 2-dimensional system.

#### **Definition**
The space format is a **string representation** of a conjunction of inequalities, which define valid constraints on state variables.  
Each inequality must:
- Use **valid state variables** (e.g., `S1`, `S2`, `A1`, `D1`).
- Be expressed in **polynomial form** (no variables on the right side of inequalities).
- Only use **conjunctions (`and`)**, as disjunctions (`or`) are not supported.
- Use **mathematical operators** such as `+`, `-`, `*`, `**`, `<=`, and `>=`.

#### **Valid Examples**
Below are some correctly formatted examples that conform to the space format for a 2-dimensional system:

- `S1 <= 100 and S2 >= 0`  
  $\rightarrow$ Constraint specifying `S1` should be at most `100`, and `S2` should be non-negative.  
- `S1 + S2 <= 100`  
  $\rightarrow$ The sum of `S1` and `S2` should not exceed `100`.  
- `S1 >= 10 and S1 <= 20` (equivalent to `10 <= S1 <= 20`, both format are acceptable and treated the same)  
  $\rightarrow$ The value of `S1` should be within the range `[10, 20]`.  
- `S1**2 + S2**2 <= 25`  
  $\rightarrow$ Represents a **circle of radius 5** centered at the origin.  
- `-2 <= S1 <= 2 and -2 <= S2 <= 2`  
  $\rightarrow$ Defines a **square with side length 4**, centered at the origin.  

#### **Invalid Examples**
Below are some **incorrect** predicates that violate the space format rules, along with explanations, for a 2-dimensional system:

- **`S3 <= 100`**  
  ❌ **Invalid**: The system is **only 2-dimensional**, but `S3` is used.  
  ✅ **Fix**: Ensure the variable exists in the defined system. In this case, the system should be 3-dimensional or more.

- **`S1 <= 10 or S2 <= 10`**  
  ❌ **Invalid**: The system **only supports conjunctions (`and`)**, not disjunctions (`or`).  
  ✅ **Fix**: Rewrite the condition using only `and`. You can define two predicates in the lookup table and use their disjunction in the LTL formula.

- **`S1 + S2 >= 5 and (S1 - S2 <= 3 or S1 >= 0)`**  
  ❌ **Invalid**: **Parentheses**, **nested logical expressions**, and **disjunctions** are **not supported**.  
  ✅ **Fix**: Use separate conditions or rewrite using `and`.

- **`S1 <= 100 & S2 >= 0`**  
  ⚠️ Although this format is allowed and system would transform `&` to `and`, it is recommended to use `and` for consistency.

#### **Where is the Space Format Used?**
The space format is used in multiple sections of the system:

- **[Stochastic Dynamical System](#stochastic-dynamical-system)** → Defines system constraints (`system_space`, `initial_space`), and conditions in piece-wise `dynamics`.  
- **[Actions](#actions)** → Specifies policies in the control policy.  
- **[Specification](#specification)** → Defines atomic predicates for LTL formulas (predicates in `preposition_lookup`).

By following this format, you ensure that the system correctly interprets and processes all predicates consistently.  

### Points about defined variables

The variables generated by the system (constants) are formatter as `{signature}_{id}` whereas the variables defined by the user are formatted as `{signature}{id}`.
So it is important that you should refer to each variable you are using as below:
- For environment variables, which defines the system state: `S1`, `S2`, etc.
- For control variables, which defines the controller's output: `A1`, `A2`, etc.
- For disturbance variables, which defines the environment's stochastic behavior: `D1`.
