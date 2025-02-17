# System's output format

At the end of execution, the system produces one of the following two outputs:

- **`UNSAT`** $\rightarrow$ No certificate exists for the given constraints.
- **`SAT + Model`** $\rightarrow$ A certificate is found, and a model is provided.

The **model** consists of a list of concrete variable assignments that satisfy the constraints. Each value is represented in **preorder format**; in other words, the model provides values that can be used to reconstruct invariants, liveness, safety properties, and control policies.

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
2. **[Invariant Variables](#invariant-variables)**: These represent invariants synthesized by the system.
3. **[Liveness Variables](#liveness-variables)**: These belong to the liveness part of the certificate, known as $V^{live}$
4. **[Safety Variables](#liveness-variables)**: These belong to the safety part of the certificate, known as $V^{safe}$.
5. **[Control Policy](#control-policy)**: The control policy that is synthesized by the system (_optional_, only in control synthesis examples).


### Boundary Variables

These variables appear in constraints but are not part of the certificate itself. They are used to define key parameters in the verification process:

| Variable Name | Symbol in Paper            | Description                                                                                                             |
|---------------|----------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Beta_safe     | $\beta$                    | A constant used in the bounded differences condition of the safety certificate, ensuring changes remain within a bound. |
| Delta_live    | $M^{L}$                    | A constant bounding the maximum allowed change (increase) for the liveness certificate.                                 |
| Delta_safe*   | $M^{S}$, $M$               | A constant bounding the maximum allowed change (increase) for the safety certificate, as part of the SafetyCond.        |
| Epsilon_live  | $\epsilon^{L}$             | A constant ensuring the strict expected decrease in expectation for the liveness certificate.                           |
| Epsilon_safe  | $\epsilon^{S}$, $\epsilon$ | A constant ensuring the strict expected decrease in expectation for the safety certificate, as part of the SafetyCond.  |
| Eta_safe      | $\eta^{S}$, $\eta$         | A constant defining an upper bound for the safety certificate at initial states.                                        |

> [!NOTE] 
> Delta_safe (appeared as $M^{S}$) is always hardcoded as 1 and does not appear in the model.


### Invariant Variables

These represent invariants synthesized by the system, which define where conditions associated to each state must be hold.
- Format: `I_{i}_{j}`
- i $\rightarrow$ The state index in the automaton.
- j $\rightarrow$ The coefficient index in the invariant template.

To interpret the invariant variables for a 1D system, the following formula can be used:

$$
\forall^{i \in Q} I_{i}(S) = \sum_{j=1}^{n+1} I_{i, j} \cdot S1^{j-1}
$$

For the example above, where:
- I_0_1 = 146.0 
- I_0_2 = 1.0 
- I_1_1 = 0.0 
- I_1_2 = 0.0

It would be interpreted as:

$$
I_{q=0}(S) = 146.0 + 1.0 \cdot S1
$$

$$
I_{q=1}(S) = 0.0
$$

> [!NOTE]
> Although invariants are optional, they are used in all of our benchmarks.


### Liveness Variables

These belong to the liveness part of the certificate, known as $V^{live}$.
- Format: `V_live{b}_{i}_{j}`
- b $\rightarrow$ The Büchi set index (always 0 when using LDBA).
- i $\rightarrow$ The state index in the automaton.
- j $\rightarrow$ The coefficient index in the certificate template.

To interpret the liveness variables for a 1D system, the following formula can be used:

$$
\forall^{i \in Q} V_{live0, i}(S) = \sum_{j=1}^{n+1} V_{live0, i, j} \cdot S1^{j-1}
$$

For the example above, where:
- V_live0_0_1 = 4703.0
- V_live0_0_2 = 24.0
- V_live0_1_1 = 600.0
- V_live0_1_2 = -4.0

It would be interpreted as:

$$
V_{live0, q=0}(S) = 4703.0 + 24.0 \cdot S1
$$

$$
V_{live0, q=1}(S) = 600.0 - 4.0 \cdot S1
$$


### Safety Variables

These belong to the safety part of the certificate, known as $V^{safe}$.
- Format: `V_safe_{i}_{j}` 
- i $\rightarrow$ The state index in the automaton.
- j $\rightarrow$ The coefficient index in the certificate template.

To interpret the safety variables for a 1D system, the following formula can be used:

$$
\forall^{i \in Q} V_{safe, i}(S) = \sum_{j=1}^{n+1} V_{safe, i, j} \cdot S1^{j-1}
$$

For the example above, where:
- V_safe_0_1 = - (151.0 / 8.0)
- V_safe_0_2 = (5.0 / 16.0)
- V_safe_1_1 = - (151.0 / 8.0)
- V_safe_1_2 = (5.0 / 16.0)

It would be interpreted as:

$$
V_{safe, q=0}(S) = - \frac{151.0}{8.0} + \frac{5.0}{16.0} \cdot S1
$$

$$
V_{safe, q=1}(S) = - \frac{151.0}{8.0} + \frac{5.0}{16.0} \cdot S1
$$


### Control Policy

This component is only present in control synthesis examples. It specifies a policy synthesized by the system.
- Format: `P{i}_{j}`
- i $\rightarrow$ The state index in the automaton.
- j $\rightarrow$ Coefficient index in the policy template.

An example of the system's output for a control synthesis example is as follows:

```text
+ Polyhorn solver completed.
  + Satisfiability: sat
    Model:
           Beta_safe: (/ 7.0 16.0)
           Delta_buchi: 2.0
           Epsilon_buchi: 1.0
           Epsilon_safe: (/ 1.0 8.0)
           Eta_safe: (- (/ 43.0 4.0))
           I_0_1: 146.0
           I_0_2: 1.0
           I_1_1: 0.0
           I_1_2: 0.0
           P_1_1: (- 2.0)
           P_1_2: 0.0
           P_2_1: (- 2.0)
           P_2_2: 0.0
           V_buchi0_0_1: 293.0
           V_buchi0_0_2: 2.0
           V_buchi0_1_1: 0.0
           V_buchi0_1_2: 0.0
           V_safe_0_1: (- 49.0)
           V_safe_0_2: (/ 1.0 2.0)
           V_safe_1_1: (- (/ 787.0 16.0))
           V_safe_1_2: (/ 1.0 2.0)
```

To interpret the control policy variables for a 1D system, the following formula can be used:

$$
\forall^{i \in Q} P_{i}(S) = \sum_{j=1}^{n+1} P_{i, j} \cdot S1^{j-1}
$$


For the example above, where:
- P_1_1 = -2.0
- P_1_2 = 0.0
- P_2_1 = -2.0
- P_2_2 = 0.0

It would be interpreted as:

$$
P_{1}(S) = -2.0
$$

$$
P_{2}(S) = -2.0
$$


