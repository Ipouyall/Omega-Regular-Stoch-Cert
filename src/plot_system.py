import numpy as np
import matplotlib.pyplot as plt

# Define the system of equations
def update_system_1(X, Y):
    X_new = X + 0.01 * (-0.5 * X - 0.5 * Y + 0.5 * X * Y)
    Y_new = Y + 0.01 * (1 - 0.5 * Y)
    return X_new, Y_new

def update_system_2(X, Y):
    X_new = 0.5 * X - X * Y
    Y_new = -0.5 * Y + X * Y
    return X_new, Y_new

# Create a grid of points for X and Y
x_vals = np.linspace(-3, 3, 25)
y_vals = np.linspace(-3, 3, 25)
X, Y = np.meshgrid(x_vals, y_vals)

# Compute the updates
X_new, Y_new = update_system_2(X, Y)

# Compute the difference (for plotting the vector field)
U = X_new - X
V = Y_new - Y

# Create the vector field plot
plt.figure(figsize=(12, 12))
plt.quiver(X, Y, U, V, angles="xy")
plt.title('Vector Field of the System (Example two)')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)
plt.xlim(-3, 3)
plt.ylim(-3, 3)
plt.show()
