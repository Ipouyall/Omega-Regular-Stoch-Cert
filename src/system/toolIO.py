from dataclasses import dataclass
import json
import yaml

from . import logger
from .action import SystemControlPolicy
from .config import SynthesisConfig
from .dynamics import SystemDynamics
from .equation import Equation
from .noise import SystemStochasticNoise
from .space import Space


@dataclass
class ToolInput:
    """
    Combines all the inputs required by the system into a single dataclass to be passed to the tool.

    Attributes:
        state_space (Space): The state space and its dimensionality.
        action_policy (SystemControlPolicy): The action space and its dimensionality.
        disturbance (SystemStochasticNoise): The stochastic disturbance space and its dimensionality.
        dynamics (SystemDynamics): The system dynamics function.
        initial_states (Space): The initial set of states defined by inequalities.
        target_states (Space): The target set of states defined by inequalities.
        unsafe_states (Space): The unsafe set of states defined by inequalities.
        probability_threshold (float): The probability threshold for system safety, in the range [0, 1).
        synthesis_config (SynthesisConfig): Configuration settings for the synthesis, including max polynomial degree and expected values.
    """
    state_space: Space
    action_policy: SystemControlPolicy
    disturbance: SystemStochasticNoise
    dynamics: SystemDynamics  # todo: need to specify input format for this
    initial_states: Space
    target_states: Space
    unsafe_states: Space
    probability_threshold: float
    synthesis_config: SynthesisConfig
# in input file: Omit `action_policy` field or use empty string if you want to learn the policy, for verification, provide your policy


class Parser:
    __organization = {
      "states": [
        "space_dimension", "system_space", "initial_space", "target_space", "unsafe_space"
      ],
      "actions": ["space", "space_dimension", "control_policy"],
      "disturbance": ["dimension", "distribution_name", "disturbance_parameters", "seed"],
      "system_dynamic": [],
      "RASM_config": ["probability_threshold"],
      "synthesis_config": [],
    }

    def __init__(self, *input_files: str):
        if not input_files:
            raise ValueError("At least one input file must be provided.")
        self.input_files = input_files

    @classmethod
    def _parse_json(cls, *file_path: str) -> dict:
        _structure = {}
        for file in file_path:
            with open(file, "r") as f:
                _data = json.load(f)
                for key, value in _data.items():
                    if key not in _structure:
                        _structure[key] = value
                        continue
                    if isinstance(value, dict):
                        _structure[key].update(value)
                    elif isinstance(value, list):
                        _structure[key].extend(value)
                    else:
                        _structure[key] = value
        return _structure

    @classmethod
    def _parse_yaml(cls, *file_path: str) -> dict:
        _structure = {}
        for file in file_path:
            with open(file, "r") as f:
                _data = yaml.safe_load(f)
                for key, value in _data.items():
                    if key not in _structure:
                        _structure[key] = value
                        continue
                    if isinstance(value, dict):
                        _structure[key].update(value)
                    elif isinstance(value, list):
                        _structure[key].extend(value)
                    else:
                        _structure[key] = value
        return _structure

    @classmethod
    def _process_dict_to_tool_input(cls, data: dict) -> ToolInput:
        state_space = Space(
            dimension=data["states"]["space_dimension"],
            inequalities=data["states"]["system_space"]
        )
        initial_space = Space(
            dimension=data["states"]["space_dimension"],
            inequalities=data["states"]["initial_space"]
        )
        target_space = Space(
            dimension=data["states"]["space_dimension"],
            inequalities=data["states"]["target_space"]
        )
        unsafe_space = Space(
            dimension=data["states"]["space_dimension"],
            inequalities=data["states"]["unsafe_space"]
        )

        action_policy = SystemControlPolicy(
            action_space=Space(
                dimension=data["actions"]["space_dimension"],
                inequalities=data["actions"]["space"]
            ),
            state_dimension=data["states"]["space_dimension"],
            maximal_degree=data["synthesis_config"]["maximal_polynomial_degree"],
            transitions=data["actions"]["control_policy"].get("control_policy", None)
        )

        disturbance = SystemStochasticNoise(
            dimension=data["disturbance"]["dimension"],
            distribution_name=data["disturbance"]["distribution_name"],
            distribution_generator_parameters=data["disturbance"]["disturbance_parameters"],
        )
        _system_dynamic_equations = [
            Equation() for _eq in data["system_dynamic"]["transformations"]
        ]
        system_dynamic = SystemDynamics(
            state_dimension=data["states"]["space_dimension"],
            action_dimension=data["actions"]["space_dimension"],
            disturbance_dimension=data["disturbance"]["dimension"],
            system_transformers=data["system_dynamic"]["transformations"]
        )

        synthesis_config = SynthesisConfig(
            maximal_polynomial_degree=data["synthesis_config"]["maximal_polynomial_degree"],
            expected_values=data["synthesis_config"]["expected_values"],
            theorem_name=data["synthesis_config"]["theorem_name"],
            solver_name=data["synthesis_config"]["solver_name"]
        )


        return ToolInput(
            state_space=state_space,
            action_policy=action_policy,
            disturbance=disturbance,
            dynamics=system_dynamic,
            initial_states=initial_space,
            target_states=target_space,
            unsafe_states=unsafe_space,
            probability_threshold=data["RASM_config"]["probability_threshold"],
            synthesis_config=synthesis_config
        )


    def parse(self) -> ToolInput:
        _structure = {k: {} for k in self.__organization.keys()}
        json_files = []
        yaml_files = []
        for file in self.input_files:
            if file.endswith(".json"):
                json_files.append(file)
            elif file.endswith(".yaml") or file.endswith(".yml"):
                yaml_files.append(file)
            else:
                logger.warning(f"Unsupported file format; ignoring the file. ({file})")

        if json_files:
            _structure.update(self._parse_json(*json_files))
        if yaml_files:
            _structure.update(self._parse_yaml(*yaml_files))
        return self._process_dict_to_tool_input(_structure)


