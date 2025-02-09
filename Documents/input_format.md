# System Documentation

The input file consists of 5 subsections:

1. **Stochastic Dynamical System**
2. **Actions**
3. **Disturbance**
4. **Specification**
5. **Synthesis Config**

You can use two organization, the first option is to define all sections is a file, 
and the second option is to split sections between multiple files. Moreover, you can use JSON or YAML format.

> [!TIP]
> For the webUI version, don't split each subsection sections to multiple files.

> [!TIP]
> System always assumes the inputs are valid and may not check for all errors before running the system.

Here we discuss how each section should be defined.

## Stochastic Dynamical System

This section defined the whole system schema, including the dynamics of the system, system's dimensions, noise dimensions, control dimensions, etc.
An example for the format of this section is as follows:

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

- **state_space_dimension:** The dimension of the state space.
- **control_space_dimension:** The dimension of the control space. your policy is later defined as `π: Dim(StateSpace) -> Dim(ControlSpace)`.
- **disturbance_space_dimension:** The dimension of the disturbance space.
- **system_space:** The constraints on the state space, which defines the system boundaries. The constraints should be defined as inequalities in the state variables.
- **dynamics:** A list of piece-wise polynomial transformations, which represent the system's dynamics. Each transformation should have a _condition_ field and a _transforms_ field. The _condition_ field should be a predicate in the state variables, and the _transforms_ field should be a list of strings, each string represents a polynomial in the state variables, action variables, and disturbance variables.

### How to specify each variable for system
#### How to specify each state dimension
To specify each state dimension's in the system dynamics for an _n_ dimensional environment, you can use variables below:
$$
\begin{align*}
\mathbf{S} &= \begin{bmatrix} S1 & S2 & \ldots & SN \end{bmatrix}
\end{align*}
$$

For example, `S1` refers to the first state variable, `S2` refers to the second state variable, and so on.

#### How to specify each action dimension
To specify each action dimension's in the system dynamics for an _m_ dimensional environment, you can use variables below:
$$
\begin{align*}
\mathbf{A} &= \begin{bmatrix} A1 & A2 & \ldots & Am \end{bmatrix}
\end{align*}
$$

For example, `A1` refers to the first action variable, `A2` refers to the second action variable, and so on.

#### How to specify each disturbance dimension
To specify each disturbance dimension's in the system dynamics for an _k_ dimensional environment, you can use variables below:
$$
\begin{align*}
\mathbf{D} &= \begin{bmatrix} D1 & D2 & \ldots & Dk \end{bmatrix}
\end{align*}
$$

For example, `D1` refers to the first disturbance variable, `D2` refers to the second disturbance variable, and so on.

### How to specify each dynamics

Dynamics of a system should be defined as a list of piece-wise polynomial transformations. Each transformation should have a _condition_ field and a _transforms_ field.

#### How to specify the condition
The _condition_ field should be a predicate in the state variables, presented as a string. They should use the predicate's valid format and be defined over state variables.

Some examples of valid conditions for a 2-dimensional systems are:
- `S1 <= 100`
- `S1 + S2 <= 100`
- `S1**2 + S2**2 <= 100` $\rightarrow$ This is a circle with radius 10 centered at the origin.
- `-2 <= S1 <= 2 and -2 <= S2 <= 2` $\rightarrow$ This is a square with side length 4 centered at the origin.
Some examples of invalid conditions for a 2-dimensional systems are:
- `S3 <= 100` $\rightarrow$ This is invalid because there is no `S3` variable. Note that the system is 2-dimensional.
- `S1 <= 10 or S2 <= 10` $\rightarrow$ Note that the token "or" is not defined for our parser. Only conjunctions are allowed.
- `S1 + S2 <= 2*S1 + S2**2` $\rightarrow$ This is invalid as our system won't consider variables at both sides of the inequality.

> [!TIP]
> If your system has only one piece-wise transformation, in other words, you don't need to use the piece-wise option, use an always true condition for the _condition_ field, such as `0 <= 1`.

#### How to specify the transforms
For a system with _n_ state variables, you should provide _n_ equations in the _transforms_ field. Each equation should be a polynomial in the state variables, action variables, and disturbance variables.
Each equation should be defined as a string, where the variables are defined as `S1`, `S2`, `S3`, etc. for state variables, `A1`, `A2`, `A3`, etc. for action variables, and `D1`, `D2`, `D3`, etc. for disturbance variables.
Consider the example dynamics below for a system with 3 state variables:
```json
{
  "stochastic_dynamical_system": {
    "state_space_dimension": 3,
    "control_space_dimension": 2,
    "disturbance_space_dimension": 1,
    "system_space": "...",
    "initial_space": "...",
    "transforms": [
      "T1",
      "T2",
      "T3"
    ]
  }
}
```
We can define:

$$
\begin{align*}
S^{'}_1 = T1(S,A,D) \\
S^{'}_2 = T2(S,A,D) \\
S^{'}_3 = T3(S,A,D) \\
\end{align*}
$$

Where:

$$
\begin{align*}
\mathbf{S} &= \begin{bmatrix} S_1 & S_2 & S_3 \end{bmatrix}
\end{align*}
$$

$$
\begin{align*}
\mathbf{A} &= \begin{bmatrix} A_1 & A_2 \end{bmatrix}
\end{align*}
$$

$$
\begin{align*}
\mathbf{D} &= \begin{bmatrix} D_1 \end{bmatrix}
\end{align*}
$$



## Actions
The complete format of this section is as follows:

```json
{
  "actions": {
    "maximal_polynomial_degree": 3,
    "control_policy": []
  }
}
```

- **maximal_polynomial_degree:** The maximal degree of the polynomial that can be used in the control policy.
- **control_policy:** A list of strings, each string represents a polynomial in the control policy. The variables in the polynomial should be defined as `S1`, `S2`, `S3`, etc.

Our proposed system can work in three modes: 
- [Policy Synthesis](#policy-synthesis)
- [Policy Verification](#policy-verification)
- [System Verification](#system-verification)

> [!NOTE]
> Since in none of our examples we have used policy validation, in this version, this option is disabled and the _control_policy_ field is always an empty list.

### Policy synthesis
<a name="policy-synthesis"></a>
For policy synthesis, you should provide _control_policy_ as an empty list or just exclude this.
The system would automatically synthesize the control policy, using polynomial degree _maximal_polynomial_degree_ or extract constants for the provided policy template and tries to propose values for these constants.

An example of the _action_ section for this setting is as follows:

```json
{
  "actions": {
    "maximal_polynomial_degree": 2,
    "control_policy": []
  }
}
```


> [!TIP]
> If the _maximal_polynomial_degree_ is not provided, the system would use the _maximal_polynomial_degree_ provided in the _synthesis_config_ section.

> [!TIP]
> Providing the _actions_ section is optional, as the system can generate the policy template automatically, and having assumption for the template degree.


### Policy verification
<a name="policy-verification"></a>
For policy verification, you should provide _control_policy_ as a list of strings, each string represents a polynomial in the control policy.
Please note that index i in the list should represent the polynomial for the i-th state variable. the Actions for `control_space_dimension = m` are presented in dynamics as below:

$$
\begin{align*}
\mathbf{control ~policy} &= \begin{bmatrix} A1 & A2 & \ldots & Am \end{bmatrix}
\end{align*}
$$

Although _maximal_polynomial_degree_ seems not necessary for this setting, you should provide to enhance documentation of your sample.

> [!IMPORTANT]
> This setting is not supported in the current version of the system. You can directly insert the control policy in the dynamics section.

### SYStem verification
<a name="system-verification"></a>
For system verification, you won't have any actions in the system.



## Disturbance
The complete format of this section is as follows:

```json
{
  "disturbance": {
    "distribution_name": "<the name of the distributions>",
    "disturbance_parameters": {}
  }
}
```

In this section, you define characteristics of the disturbance. Although you can have as many distributions as you want, 
this implementation consider only one distribution. The _distribution_name_ should be one of the following:
- **normal**
- **uniform**

After specifying the _distribution_name_, you should provide the parameters of the distribution in the _disturbance_parameters_ field.
Please refer to the description of each distribution for more information.

> [!IMPORTANT]
> In the current version of the system, the disturbance should be always one-dimensional.

### Normal Distributions
For this distribution, you should use _normal_ as the _distribution_name_ and for _disturbance_parameters_ should have two fields: _mean_ and _std_, which are lists of floats.

For example, for one dimensional normal distribution with `mean = 0 and standard deviation = 1`, you should provide the following:

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

### Uniform Distributions
For this distribution, you should use _uniform_ as the _distribution_name_ and for _disturbance_parameters_ should have two fields: _lower_bound_ and _upper_bound_, which are lists of floats.

For example, for one dimensional uniform distribution with `lower_bound = -2 and upper_bound = 1`, you should provide the following:

```json
{
  "disturbance": {
    "distribution_name": "uniform",
    "disturbance_parameters": {
      "lower_bound": [-2],
      "upper_bound": [1]
    }
  }
}
```

## Specification
An example of the complete format of this section is as follows:

```json
{
  "specification": {
    "ltl_formula": "(G F a) -> (G F b)",
    "preposition_lookup": {
      "a": "S1 > 0",
      "b": "S2 > 0"
    }
  }
}
```

- **ltl_formula:** The LTL formula.
- **predicate_lookup:** A dictionary where the keys are the atomic propositions in the LTL formula and the values are the predicates that define them. The predicates should be defined as inequalities in the state variables.

Note that **predicate_lookup** is an optional field, and you may not provide it. Consider the example below:
    
```json
{
    "specification": {
        "ltl_formula": "(G F 'S1 > 0') -> (G F 'S2 > 0')"
    }
}
```

If you with to use **predicate_lookup**, you should only use `a-z` as atomic propositions in the LTL formula.

## Synthesis Config

An example of a complete form of this section is as follows:

```json
{
  "synthesis_config": {
    "use_linear_invariant": false,
    "maximal_polynomial_degree": 1,
    "probability_threshold": 0.99,
    "theorem_name": "farkas",
    "solver_name": "z3",
    "owl_path": "<path to the owl binary in your system>"
  }
}
```

There exist several parameters in this section:

- **use_linear_invariant:** A boolean value that determines whether the system should use a linear invariant or not. If it set to `true`, the system would synthesize a linear invariant for the system. If it set to `false`, the system would synthesize an invariant for the system as well.
- **maximal_polynomial_degree:** The maximal degree of the polynomial. This parameter is used to synthesize certificate's template, inform the solver, and potentially it might be used to determine the degree of the polynomial in the control policy (if not provided there).
- **probability_threshold:** The probability threshold.
- **theorem_name:** The name of the theorem to be used. This can be one of `farkas`, `handelman`, or `putinar`.
- **solver_name:** The name of the solver to be used. It can be one of `z3` or `mathsat`. Based on the OS, you might be limited to `z3`.
- **owl_path:** The path to the owl binary in your system, to convert the LTL formula to an automaton.

> [!TIP]
> If you specify _hoa_path_ in the _synthesis_config_ section, the system would read the provided HOA file and consider that automata, instead of converting the LTL formula to an automaton.
