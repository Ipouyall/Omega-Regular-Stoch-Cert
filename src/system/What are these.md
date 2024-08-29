# State

System state is defined as a vector of values, using notation below ro represent them:

$$
\begin{align*}
\mathbf{State_s} &= \begin{bmatrix} S1 & S2 & \ldots & Sn \end{bmatrix}
\end{align*}
$$

Where $S1, S2, \ldots, Sn$ are the values of the state and `n` is the state space dimensionality.

---

# Action Policy

Control action policy of the system is defined as a vector of values, using notation below to represent them:

$$
\begin{align*}
\mathbf{Action_A} &= \begin{bmatrix} A1 & A2 & \ldots & Am \end{bmatrix}
\end{align*}
$$

Where $A1, A2, \ldots, Am$ are the values of the action, defined as a polynomial operation based on the current `state values`.
Each constant is being named as $A{dim}\_{index}$ for example $A1\_0$ is the first constant of the first action dimension.

For policy calculation, where the policy is unknown, these equations are generated based on the 
_State space dimensionality_, _Action space dimensionality_, and _maximal polynomial degree_.

---

