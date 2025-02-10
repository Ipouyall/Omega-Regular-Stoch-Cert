# System's output format

At the end, the system would output **UNSAT** if there is no certificate, and **SAT + Model** if there is a certificate. 
The model is a list of assignments to the variables that make the formula true, where each value presented in preorder format.

An example of a model is as below:

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

The model consists of the following 4+1 parts:
1. **Boundary variables**: These are the variables that are used in constraints and are not part of the certificate, such as $\eta$, $\epsilon$, $\Delta$, $\beta$, and $M$. 
2. **Invariant**: The invariants that are synthesized by the system. They are presented in the format of `I_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the constant in the invariant template. Although this part is optional, we used invariant in all of our benchmarks.
3. **Liveness variables**: The liveness variables that belong to the liveness part of the certificate. They are presented in the format of `V_live_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the constant in the certificate template.
4. **Safety variables**: The safety variables that belong to the safety part of the certificate. They are presented in the format of `V_safe_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the constant in the certificate template.
5. **Control policy**: The control policy that is synthesized by the system (_optional_, only in control synthesis examples). They are presented as `P{a|b}_{i}_{j}` where $a$ means acceptance policy, $b$ means buchi/live policy, $i$ is the buchi set index and is always 1, and $j$ is the index of the constant in the policy template.


[//]: # (Remember that Delta_safe is hard-coded as 1, this should be mentioned somewhere.)


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
