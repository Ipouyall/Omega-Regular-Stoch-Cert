import numpy as np
import matplotlib.pyplot as plt


def dynamics(S1, S2):
    dS1 = 0.1 * S2
    dS2 = (-S1 + (1 - S1 ** 2) * S2) * 0.1
    return dS1, dS2


def plot_system(boundary_min, boundary_max, grid_points=50, highlight_region=None):
    S1 = np.linspace(boundary_min, boundary_max, grid_points)
    S2 = np.linspace(boundary_min, boundary_max, grid_points)
    S1_grid, S2_grid = np.meshgrid(S1, S2)

    U, V = dynamics(S1_grid, S2_grid)

    norm = np.sqrt(U ** 2 + V ** 2)
    U /= norm + 1e-5
    V /= norm + 1e-5

    plt.figure(figsize=(10, 8))
    plt.streamplot(S1, S2, U, V, color='orange', linewidth=2)
    plt.title(f"Streamlines of the System (Boundaries: {boundary_min} to {boundary_max})")
    plt.xlabel("S1")
    plt.ylabel("S2")
    plt.xlim(boundary_min, boundary_max)
    plt.ylim(boundary_min, boundary_max)
    plt.grid()
    if highlight_region is not None:
        rect_x_min, rect_x_max = highlight_region[0]
        rect_y_min, rect_y_max = highlight_region[1]
        plt.gca().add_patch(plt.Rectangle(
            (rect_x_min, rect_y_min),
            rect_x_max - rect_x_min,
            rect_y_max - rect_y_min,
            color='lightgreen', alpha=0.3, label="Highlighted rectangle"))
    plt.legend()
    plt.show()


plot_system(-5, 5, highlight_region=[[-1.2,-0.9], [-2.9, -2]])
