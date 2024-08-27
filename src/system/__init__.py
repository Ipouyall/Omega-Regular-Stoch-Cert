from dataclasses import dataclass
from logging import getLogger

from src.system.action import SystemActionPolicy
from src.system.config import SynthesisConfig
from src.system.dynamics import SystemDynamics
from src.system.noise import SystemStochasticNoise
from src.system.space import Space


logger = getLogger(__name__)


@dataclass
class ToolInput:
    """
    Combines all the inputs required by the system into a single dataclass to be passed to the tool.

    Attributes:
        state_space (Space): The state space and its dimensionality.
        action_policy (SystemActionSpace): The action space and its dimensionality.
        disturbance (SystemStochasticNoise): The stochastic disturbance space and its dimensionality.
        dynamics (SystemDynamics): The system dynamics function.
        initial_states (Space): The initial set of states defined by inequalities.
        target_states (Space): The target set of states defined by inequalities.
        unsafe_states (Space): The unsafe set of states defined by inequalities.
        probability_threshold (float): The probability threshold for system safety, in the range [0, 1).
        synthesis_config (SynthesisConfig): Configuration settings for the synthesis, including max polynomial degree and expected values.
    """
    state_space: Space  # The state space and its dimensionality.
    action_policy: SystemActionPolicy  # The action space and its dimensionality.
    disturbance: SystemStochasticNoise  # The stochastic disturbance space and its dimensionality.
    dynamics: SystemDynamics  # The system dynamics function.
    initial_states: Space  # The initial set of states defined by inequalities.
    target_states: Space  # The target set of states defined by inequalities.
    unsafe_states: Space  # The unsafe set of states defined by inequalities.
    probability_threshold: float  # The probability threshold for system safety, in the range [0, 1).
    synthesis_config: SynthesisConfig  # Configuration settings for the synthesis, including max polynomial degree and expected values.