import numpy as np
import matplotlib.pyplot as plt

def update_spiraling_system(X, Y):
    X_new = 0.9 * X - 0.4 * Y
    Y_new = 0.4 * X + 0.9 * Y
    return X_new, Y_new

def update_spiraling_system2(X, Y, tau=0.05):
    A = np.array([[1, -2],
                  [1, -1]])
    X_new = X + (A[0, 0] * X + A[0, 1] * Y) * tau
    Y_new = Y + (A[1, 0] * X + A[1, 1] * Y) * tau
    return X_new, Y_new

x_vals = np.linspace(-3, 3, 25)
y_vals = np.linspace(-3, 3, 25)
X, Y = np.meshgrid(x_vals, y_vals)

X_new, Y_new = update_spiraling_system2(X, Y)
U = X_new - X
V = Y_new - Y

plt.figure(figsize=(12, 12))
plt.quiver(X, Y, U, V, angles="xy")

plt.axhline(0, color='black', linewidth=1)
plt.axvline(0, color='black', linewidth=1)
plt.fill_betweenx([0, 3], 0, 3, color='lightgreen', alpha=0.3, label='Quadrant 1 (Buchi Set)')
plt.fill_betweenx([-3, 0], -3, 0, color='lightcoral', alpha=0.3, label='Quadrant 3 (Buchi Set)')

plt.title('Vector Field of the Spiraling System with Buchi Sets')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)
plt.xlim(-3, 3)
plt.ylim(-3, 3)
plt.legend()
plt.show()