import numpy as np
import matplotlib.pyplot as plt

alpha = -1 / 32
beta = 4787 / 512
t_ext = 300  # Reference external temperature

def updated_dynamics(X, t_ext, alpha, beta):
    return X - (1 / 100) * (X - t_ext) + (alpha * X + beta)

x_vals = np.linspace(280, 320, 100)
x_next_updated = updated_dynamics(x_vals, t_ext, alpha, beta)

spec_a = 298
spec_b = 292

x_vals_arrow = np.linspace(280, 320, 15)
x_grid, x_next_grid = np.meshgrid(x_vals_arrow, x_vals_arrow)

x_next_arrows = updated_dynamics(x_grid, t_ext, alpha, beta)

plt.figure(figsize=(12, 6))
plt.plot(x_vals, x_next_updated, label=r"Dynamics: $X_{t+1} = X_t - \frac{1}{100}(X_t - t_{ext}) + (\alpha X_t + \beta)$")
plt.axhline(spec_a, color="red", linestyle="--", label="Boundary: $a$ ($S1 \geq 298$)")
plt.axhline(spec_b, color="blue", linestyle="--", label="Boundary: $b$ ($S1 \leq 292$)")
plt.fill_between(x_vals, spec_b, spec_a, color="yellow", alpha=0.3, label="Violation Region (!a & !b)")

for i in range(len(x_vals_arrow)):
    plt.arrow(x_vals_arrow[i], x_vals_arrow[i],
              0, x_next_arrows[i, i] - x_vals_arrow[i],
              head_width=0.5, head_length=1.5, fc='black', ec='black')

plt.title("Visualization of Updated Dynamics with Specification and Arrows")
plt.xlabel("State $S1$")
plt.ylabel("Next State $S1'$")
plt.legend()
plt.grid()
plt.show()