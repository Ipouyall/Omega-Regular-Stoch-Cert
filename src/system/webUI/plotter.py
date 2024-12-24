import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, lambdify

from ..dynamics import ConditionalDynamics


def _parse_dynamics_sympy(dynamics_strings):
    """
    Parses a list of dynamics equations using SymPy and returns a callable function.
    """
    S1, S2 = symbols("S1 S2")
    dynamics_exprs = [lambdify((S1, S2), expr, "numpy") for expr in dynamics_strings]
    return lambda S1, S2: (dynamics_exprs[0](S1, S2), dynamics_exprs[1](S1, S2))


def _plot_system(dynamics_strings, boundary_min, boundary_max, grid_points=50, highlight_region=None):
    """
    Plots the system's streamlines based on dynamics provided as strings.
    """
    dynamics = _parse_dynamics_sympy(dynamics_strings)

    S1 = np.linspace(boundary_min, boundary_max, grid_points)
    S2 = np.linspace(boundary_min, boundary_max, grid_points)
    S1_grid, S2_grid = np.meshgrid(S1, S2)

    U, V = dynamics(S1_grid, S2_grid)

    norm = np.sqrt(U ** 2 + V ** 2)
    U /= norm + 1e-5
    V /= norm + 1e-5

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.streamplot(S1, S2, U, V, color='orange', linewidth=2)
    # ax.set_title(f"Streamlines of the System ({boundary_min} to {boundary_max})")
    ax.set_xlabel("S1")
    ax.set_ylabel("S2")
    ax.set_xlim(boundary_min, boundary_max)
    ax.set_ylim(boundary_min, boundary_max)
    ax.grid()

    if highlight_region is not None:
        for region in highlight_region:
            rect_x_min, rect_x_max = region[0]
            rect_y_min, rect_y_max = region[1]
            ax.add_patch(plt.Rectangle(
                (rect_x_min, rect_y_min),
                rect_x_max - rect_x_min,
                rect_y_max - rect_y_min,
                color='lightgreen', alpha=0.3))
    return fig

def plot_dynamics_from_conditional_eq(conditional_equations: list[ConditionalDynamics]):
    if len(conditional_equations) != 1:
        st.error("Only one conditional equation is supported for plotting.")
        return
    if len(conditional_equations[0].dynamics) != 2:
        st.error("Only two dimensional dynamics are supported for plotting.")
        return
    transformations = [f"{str(d)}-S{i}" for i, d in enumerate(conditional_equations[0].dynamics, start=1)]

    fig = _plot_system(transformations, -5, 5)
    st.pyplot(fig)



