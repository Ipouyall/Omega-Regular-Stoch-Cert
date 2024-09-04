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
Each constant is being named as $P{dim}\_{index}$ for example $P1\_0$ is the first constant of the first action dimension.

For policy calculation, where the policy is unknown, these equations are generated based on the 
_State space dimensionality_, _Action space dimensionality_, and _maximal polynomial degree_.

---

# Environment Dynamics

The environment dynamics are defined as a function that takes 
the _current state vector of values_,
_action_, and _stochastic noise values_ (disturbance)
as input and returns the next state. Expected notations for formulation are as below:

$$
\begin{align*}
\mathbf{S} &= \begin{bmatrix} S1 & S2 & \ldots & Sn \end{bmatrix}
\end{align*}
$$

$$
\begin{align*}
\mathbf{A} &= \begin{bmatrix} A1 & A2 & \ldots & Am \end{bmatrix}
\end{align*}
$$

$$
\begin{align*}
\mathbf{D} &= \begin{bmatrix} D1 & D2 & \ldots & Dk \end{bmatrix}
\end{align*}
$$

There would exist **n** equations for defining each state output dimension.

---

# Certificate

The certificate gets a system state and returns a float value.

$$
\begin{align*}
\mathbf{V(s)} &= \mathbf{Certificate}(\mathbf{State_s})
\end{align*}
$$

It expects the provided state to be a valid state vector as below:

$$
\begin{align*}
\mathbf{State_s} &= \begin{bmatrix} S_1 & S_2 & \ldots & S_n \end{bmatrix}
\end{align*}
$$

Also, the constants are being defined as:

$$
\begin{align*}
\mathbf{constants_{V(s)}} &= \begin{bmatrix} V_1 & V_2 & \ldots & V_n & V_{n+1} \end{bmatrix}
\end{align*}
$$

