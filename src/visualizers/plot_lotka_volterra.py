import matplotlib.pyplot as plt
import numpy as np

# Parameters
alpha = 2  # Prey's growth rate
beta = 0.04  # Effect of predators on prey
gamma = 1.06  # Predator's death rate
delta = 0.02  # Effect of prey on predator growth
tau = 0.1  # Sampling time
time_steps = 200  # Number of time steps
noise_std = 0.1  # Standard deviation of noise
stochastic_env = True  # Stochastic environment

# Fixed Points
x_fixed = gamma / delta  # Fixed point for prey
y_fixed = alpha / beta  # Fixed point for predator


S1 = np.zeros(time_steps)  # Prey population
S2 = np.zeros(time_steps)  # Predator population

S1[0] = x_fixed
S2[0] = y_fixed
if stochastic_env:
    S1[0] += np.random.uniform(-noise_std, noise_std)
    S2[0] += np.random.uniform(-noise_std, noise_std)

# Dynamics equations for the prey and predator
for t in range(1, time_steps):
    w1 = np.random.uniform(-noise_std, noise_std)  # Noise for prey
    w2 = np.random.uniform(-noise_std, noise_std)  # Noise for predator

    S1[t] = (1 + alpha * tau) * S1[t - 1] - beta * tau * S1[t - 1] * S2[t - 1] # Prey equation
    if stochastic_env:
        S1[t] += w1
    S1[t] = max(S1[t], 0)

    S2[t] = (1 - gamma * tau) * S2[t - 1] + delta * tau * S1[t - 1] * S2[t - 1] # Predator equation
    if stochastic_env:
        S2[t] += w2
    S2[t] = max(S2[t], 0)

# Plot Prey and Predator populations
plt.figure(figsize=(10, 6))
plt.plot(S1, label="Prey Population (X)", linewidth=2, color="orange")
plt.plot(S2, label="Predator Population (Y)", linewidth=2, color="orangered")
plt.axhline(y=x_fixed, color='red', linestyle='--', label="Fixed Point (Prey)")
plt.axhline(y=y_fixed, color='blue', linestyle='--', label="Fixed Point (Predator)")

# Add titles and labels
plt.title(f"Synchronization Towards Non-Trivial Fixed Point (stochastic: {stochastic_env})")
plt.xlabel("Time Steps")
plt.ylabel("Population Density")
plt.legend()
plt.grid()
plt.show()