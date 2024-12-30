# import numpy as np
# import matplotlib.pyplot as plt
#
#
# def dynamics(S1, S2):
#     dS1 = 0.1 * S2
#     dS2 = (-S1 + (1 - S1 ** 2) * S2) * 0.1
#     return dS1, dS2
#
#
# def plot_system(boundary_min, boundary_max, grid_points=50, highlight_region=None):
#     S1 = np.linspace(boundary_min, boundary_max, grid_points)
#     S2 = np.linspace(boundary_min, boundary_max, grid_points)
#     S1_grid, S2_grid = np.meshgrid(S1, S2)
#
#     U, V = dynamics(S1_grid, S2_grid)
#
#     norm = np.sqrt(U ** 2 + V ** 2)
#     U /= norm + 1e-5
#     V /= norm + 1e-5
#
#     plt.figure(figsize=(10, 8))
#     plt.streamplot(S1, S2, U, V, color='orange', linewidth=2)
#     plt.title(f"Streamlines of the System (Boundaries: {boundary_min} to {boundary_max})")
#     plt.xlabel("S1")
#     plt.ylabel("S2")
#     plt.xlim(boundary_min, boundary_max)
#     plt.ylim(boundary_min, boundary_max)
#     plt.grid()
#     if highlight_region is not None:
#         rect_x_min, rect_x_max = highlight_region[0]
#         rect_y_min, rect_y_max = highlight_region[1]
#         plt.gca().add_patch(plt.Rectangle(
#             (rect_x_min, rect_y_min),
#             rect_x_max - rect_x_min,
#             rect_y_max - rect_y_min,
#             color='lightgreen', alpha=0.3, label="Highlighted rectangle"))
#     plt.legend()
#     plt.show()
#
#
# plot_system(-5, 5, highlight_region=[[-1.2,-0.9], [-2.9, -2]])





# import numpy as np
# import matplotlib.pyplot as plt
#
# def dynamics_helper(transformation: str, variables: dict[str, str]):
#     for k, v in variables.items():
#         transformation = transformation.replace(k,v)
#     return eval(transformation)
#
# # def dynamics(S1, S2):
# #     fS1 = "0.1 * S2"
# #     fS2 = "(-S1 + (1 - S1 ** 2) * S2) * 0.1"
# #
# #
# #     dS1 = [
# #         [
# #             dynamics_helper(fS1, {"S1": str(s1), "S2": str(s2)})
# #             for s1,s2 in zip(ds1,ds2)
# #         ]
# #         for ds1, ds2 in zip(S1, S2)
# #     ]
# #     dS2 = [
# #         [
# #             dynamics_helper(fS2, {"S1": str(s1), "S2": str(s2)})
# #             for s1,s2 in zip(ds1,ds2)
# #         ]
# #         for ds1, ds2 in zip(S1, S2)
# #     ]
# #     dS1 = np.array(dS1)
# #     dS2 = np.array(dS2)
# #     return dS1, dS2
#
# def dynamics(S1, S2):
#     dS1 = 0.1 * S2
#     dS2 = (-S1 + (1 - S1 ** 2) * S2) * 0.1
#     return dS1, dS2
#
#
# def plot_system(boundary_min, boundary_max, grid_points=1500, highlight_region=None):
#     S1 = np.linspace(boundary_min, boundary_max, grid_points)
#     S2 = np.linspace(boundary_min, boundary_max, grid_points)
#     S1_grid, S2_grid = np.meshgrid(S1, S2)
#
#     U, V = dynamics(S1_grid, S2_grid)
#
#     norm = np.sqrt(U ** 2 + V ** 2)
#     U /= norm + 1e-5
#     V /= norm + 1e-5
#
#     plt.figure(figsize=(10, 8))
#     plt.streamplot(S1, S2, U, V, color='orange', linewidth=2)
#     plt.title(f"Streamlines of the System (Boundaries: {boundary_min} to {boundary_max})")
#     plt.xlabel("S1")
#     plt.ylabel("S2")
#     plt.xlim(boundary_min, boundary_max)
#     plt.ylim(boundary_min, boundary_max)
#     plt.grid()
#     if highlight_region is not None:
#         rect_x_min, rect_x_max = highlight_region[0]
#         rect_y_min, rect_y_max = highlight_region[1]
#         plt.gca().add_patch(plt.Rectangle(
#             (rect_x_min, rect_y_min),
#             rect_x_max - rect_x_min,
#             rect_y_max - rect_y_min,
#             color='lightgreen', alpha=0.3, label="Highlighted rectangle"))
#     plt.legend()
#     plt.show()
#
# plot_system(-5, 5, highlight_region=[[-1.2,-0.9], [-2.9, -2]])


import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, lambdify


def parse_dynamics_sympy(dynamics_strings):
    """
    Parses a list of dynamics equations using SymPy and returns a callable function.
    """
    S1, S2 = symbols("S1 S2")
    dynamics_exprs = [lambdify((S1, S2), expr, "numpy") for expr in dynamics_strings]
    return lambda S1, S2: (dynamics_exprs[0](S1, S2), dynamics_exprs[1](S1, S2))


def plot_system(dynamics_strings, boundary_min, boundary_max, grid_points=50, highlight_region=None):
    """
    Plots the system's streamlines based on dynamics provided as strings.
    """
    # Parse the dynamics
    dynamics = parse_dynamics_sympy(dynamics_strings)

    # Create grid for S1 and S2
    S1 = np.linspace(boundary_min, boundary_max, grid_points)
    S2 = np.linspace(boundary_min, boundary_max, grid_points)
    S1_grid, S2_grid = np.meshgrid(S1, S2)

    # Compute dynamics
    U, V = dynamics(S1_grid, S2_grid)

    # Normalize vectors for streamplot
    norm = np.sqrt(U ** 2 + V ** 2)
    U /= norm + 1e-5
    V /= norm + 1e-5

    # Plot streamlines
    plt.figure(figsize=(10, 8))
    plt.streamplot(S1, S2, U, V, color='orange', linewidth=2)
    plt.title(f"Streamlines of the System (Boundaries: {boundary_min} to {boundary_max})")
    plt.xlabel("S1")
    plt.ylabel("S2")
    plt.xlim(boundary_min, boundary_max)
    plt.ylim(boundary_min, boundary_max)
    plt.grid()

    # Highlight specific regions if provided
    if highlight_region is not None:
        for region in highlight_region:
            rect_x_min, rect_x_max = region[0]
            rect_y_min, rect_y_max = region[1]
            plt.gca().add_patch(plt.Rectangle(
                (rect_x_min, rect_y_min),
                rect_x_max - rect_x_min,
                rect_y_max - rect_y_min,
                color='lightgreen', alpha=0.3))

    plt.show()


# Example usage
dynamics_strings = [
    # "-0.0167 * S1 + 0.333",
    # "-0.0142 * S2"

    "-0.0183*S1 -0.3317*S2 + 0.3333",
    "0.0142*S1 - 0.0142*S2"

    # "0.2*S1 - 0.3*S2 + 0.5",
    # "0.5*S1 - 0.5*S2 + 0.5"
    #
    # "0.2*S1",
    # "0.2*S2"

    # "0.1 * S2",
    # "(-S1 + (1 - S1 ** 2) * S2) * 0.1",
]

if __name__ == "__main__":
    plot_system(
        dynamics_strings,
        boundary_min=-10,
        boundary_max=10,
        grid_points=50,
        # highlight_region=[[[-1.2, -0.9], [-2.9, -2]]]
    )