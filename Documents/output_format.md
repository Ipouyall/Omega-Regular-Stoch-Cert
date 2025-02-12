# System's output format

At the end of execution, the system produces one of the following two outputs:

- **`UNSAT`** → No certificate exists for the given constraints.
- **`SAT + Model`** → A certificate is found, and a model is provided.

The **model** consists of a list of variable assignments that satisfy the constraints. Each concrete value is represented in **preorder format**.

## Output format

A typical model output from the system (for a verification example) looks as follows:

```text
+ Polyhorn solver completed.
  + Satisfiability: sat
    Model:
           Beta_safe: (- (/ 3.0 8.0))
           Delta_live: 2.0
           Epsilon_live: 12.0
           Epsilon_safe: (/ 5.0 32.0)
           Eta_safe: (- 8.0)
           I_0_1: 146.0
           I_0_2: 1.0
           I_1_1: 0.0
           I_1_2: 0.0
           V_live0_0_1: 4703.0
           V_live0_0_2: 24.0
           V_live0_1_1: 600.0
           V_live0_1_2: (- 4.0)
           V_safe_0_1: (- (/ 151.0 8.0))
           V_safe_0_2: (/ 5.0 16.0)
           V_safe_1_1: (- (/ 151.0 8.0))
           V_safe_1_2: (/ 5.0 16.0)
```

The model consists of five main components, each serving a distinct role in the verification and synthesis process:

1. **[Boundary variables](#boundary-variables)**: These variables appear in constraints but are not part of the certificate itself, such as $\eta$, $\epsilon$, $\Delta$, $\beta$, and $M$. 
2. **[Invariant Variables](#invariant-variables)**: The invariants that are synthesized by the system. They are presented in the format of `I_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the constant in the invariant template. Although this part is optional, we used invariant in all of our benchmarks.
3. **Liveness variables**: The liveness variables that belong to the liveness part of the certificate. They are presented in the format of `V_live{b}_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, $j$ is the index of the constant in the certificate template, and $b$ is the buchi set index, which is always 0.
4. **Safety variables**: The safety variables that belong to the safety part of the certificate. They are presented in the format of `V_safe_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the constant in the certificate template.
5. **Control policy**: The control policy that is synthesized by the system (_optional_, only in control synthesis examples). They are presented as `P{a|b}_{i}_{j}` where $a$ means acceptance policy, $b$ means buchi/live policy, $i$ is the buchi set id and is always 1, and $j$ is the index of the constant in the policy template.


### Boundary Variables

These variables appear in constraints but are not part of the certificate itself. They are used to define key parameters in the verification process:

| Variable Name | Symbol in Paper            | Description                                                 |
|---------------|----------------------------|-------------------------------------------------------------|
| Beta_safe     | $M$, $M^S$, $M^L$          | A constant used in safety constraints.                      |
| Delta_live    | $\Delta^{L}$               | A parameter controlling the liveness properties.            |
| Epsilon_live  | $\epsilon^{L}$             | A small margin ensuring robustness in liveness constraints. |
| Epsilon_safe  | $\epsilon^{S}$, $\epsilon$ | A small margin ensuring robustness in safety constraints.   |
| Eta_safe      | $\eta^{S}$, $\eta$         | A parameter related to safety margin calculations.          |

> [!NOTE] 
> Delta_safe is always hardcoded as 1 and does not appear in the model.

### Invariant Variables


[//]: # (Remember that Delta_safe is hard-coded as 1, this should be mentioned somewhere.)

## Extract templates from the model

To extract the invariant's template, given the constants, for a 1D system, the following formula can be used:

$$
\forall^{i \in Q} I_{i}(S) = \sum_{j=1}^{n+1} I_{i, j} \cdot S1^{j-1}
$$

For example, in the example above, the invariant template would be:

$$
I_{0}(S) = 146.0 + 1.0 \cdot S1
$$

$$
I_{1}(S) = 0.0 + 0.0 \cdot S1
$$

The same thing is applicable to other components. For instance, the liveness template would be:

$$
V_{live0,1}(S) = 4703.0 + 24.0 \cdot S1
$$

$$
V_{live0,2}(S) = 600.0 - 4.0 \cdot S1
$$

And the safety template would be:

$$
V_{safe,1}(S) = - \frac{151.0}{8.0} + \frac{5.0}{16.0} \cdot S1
$$

$$
V_{safe,2}(S) = - \frac{151.0}{8.0} + \frac{5.0}{16.0} \cdot S1
$$

## Model's boundary variables components

This component is not part of the certificate, but it is used in the constraints. The boundary variables are:
- **Beta_safe** which is equivalent to $M$ in the paper.
- **Delta_live** which is equivalent to $\Delta_{live}$ in the paper.
- **Epsilon_live** which is equivalent to $\epsilon_{live}$ in the paper.
- **Epsilon_safe** which is equivalent to $\epsilon_{safe}$ in the paper.
- **Eta_safe** which is equivalent to $\eta_{safe}$ in the paper.
