# System's output format

At the end, the system would output **UNSAT** if there is no certificate, and **SAT + Model** if there is a certificate. 
The model is a list of assignments to the variables that make the formula true, where each value presented in preorder format.

An example of a model is as below:

```text
+ Polyhorn solver completed.
  + Satisfiability: sat
    Model:
           Beta_safe: (- (/ 2601.0 8192.0))
           Delta_buchi: 2.0
           Epsilon_buchi: 12.0
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
           V_safe_1_1: (- (/ 154623.0 8192.0))
           V_safe_1_2: (/ 1281.0 4096.0)
```

The model consists of the following 4+1 parts:
1. **Boundary variables**: These are the variables that are used in constraints and are not part of the certificate, such as $\eta$, $\epsilon$, etc.
2. **Invariant**: The invariants that are synthesized by the system. They are presented in the format of `I_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the invariant. Although this part is optional, we used invariant in all of our benchmarks.
3. **Liveness variables**: The liveness variables that belong to the liveness part of the certificate. They are presented in the format of `V_live_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the invariant.
4. **Safety variables**: The safety variables that belong to the safety part of the certificate. They are presented in the format of `V_safe_{i}_{j}`, where $i$ is present which state of the automata that the invariant belongs to, and $j$ is the index of the invariant.
5. **Control policy**: The control policy that is synthesized by the system (optional, only in control synthesis examples). They are presented as `P{a/b}_{i}_{j}` where $a$ is the state that the policy is applied to, $b$ is the index of the policy, $i$ is always 1, and $j$ is the index of the policy.


