import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

fig, ax = plt.subplots(figsize=(8, 8))

# System space
system_space_outer = Circle((0, 0), 10.01, color='darkgrey', alpha=0.9)
system_space = Circle((0, 0), 10, color='lightgrey', alpha=0.8, label="System Space")

# Unsafe space
unsafe_space_outer = Circle((0, 0), 10, color='red', alpha=0.4, label="Unsafe Space")
unsafe_space_inner = Circle((0, 0), 9, color='lightgrey', alpha=0.9)

# Initial space
initial_inner_radius = np.sqrt(16)
initial_outer_radius = np.sqrt(25)
initial_space_outer = Circle((0, 0), initial_outer_radius, color='blue', alpha=0.7, label="Initial Space")
initial_space_inner = Circle((0, 0), initial_inner_radius, color='lightgrey', alpha=0.99)

# Target space
target_space = Circle((0, 0), 4, color='green', alpha=0.7, label="Target Space")

ax.add_patch(system_space_outer)
ax.add_patch(system_space)

ax.add_patch(unsafe_space_outer)
ax.add_patch(unsafe_space_inner)

ax.add_patch(initial_space_outer)
ax.add_patch(initial_space_inner)

ax.add_patch(target_space)


ax.set_xlim(-11, 11)
ax.set_ylim(-11, 11)
ax.set_aspect('equal')

plt.grid(True)
plt.xlabel("S1")
plt.ylabel("S2")
# set legend to upper-right corner
plt.legend(loc='upper right')
plt.title('Visualization of the safe linear system')
plt.show()
