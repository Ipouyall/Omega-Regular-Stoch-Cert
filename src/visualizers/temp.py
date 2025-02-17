import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


# Updated dynamics function
def updated_dynamics(S1, S2):
    dS1 = 0.2 * S1 - 0.3 * S2 + 0.5
    dS2 = 0.5 * S1 - 0.5 * S2 + 0.5

    # Triangular obstacle effects
    if (S1**2 + S2**2 >= 91):  # Upper left triangular obstacle
        dS1 = -0.1*S1
        dS2 = -0.1*S2

    return dS1, dS2


# Function to plot the updated system
def plot_updated_system(boundary_min, boundary_max, grid_points=50, highlight_regions=None):
    S1 = np.linspace(boundary_min, boundary_max, grid_points)
    S2 = np.linspace(boundary_min, boundary_max, grid_points)
    S1_grid, S2_grid = np.meshgrid(S1, S2)

    U, V = np.zeros_like(S1_grid), np.zeros_like(S2_grid)
    for i in range(S1_grid.shape[0]):
        for j in range(S2_grid.shape[1]):
            U[i, j], V[i, j] = updated_dynamics(S1_grid[i, j], S2_grid[i, j])

    norm = np.sqrt(U ** 2 + V ** 2)
    U /= norm + 1e-5
    V /= norm + 1e-5

    plt.figure(figsize=(10, 10))
    plt.streamplot(S1, S2, U, V, color='orange', linewidth=1)
    # plt.title("Streamlines of the Updated System with Obstacles")
    plt.xlabel("S1")
    plt.ylabel("S2")
    plt.xlim(boundary_min, boundary_max)
    plt.ylim(boundary_min, boundary_max)
    plt.grid()


    plt.show()


# Define the triangular obstacle regions
upper_left_triangle = [[-10, 10], [-10, 3], [-3, 10]]
lower_right_triangle = [[10, -10], [10, -3], [3, -10]]

# Plot the system
plot_updated_system(
    -10, 10,
    grid_points=50,
    # highlight_regions=[upper_left_triangle, lower_right_triangle]
)