from dataclasses import dataclass
import json
import yaml

from . import logger
from .dynamics import ConditionalDynamics
from .polynomial.equation import Equation
from .space import extract_space_inequalities


@dataclass
class ToolInput:
    """
    Combines all the inputs required by the system into a single dataclass to be passed to the tool.

    Attributes:

    """
    actions_pre: dict
    disturbance_pre: dict
    sds_pre: dict
    synthesis_config_pre: dict
    specification_pre: dict
    system_space_pre: str
    initial_space_pre: str
    enable_linear_invariants: bool

    # in input file: Omit `action_policy` field or use empty string if you want to learn the policy, for verification, provide your policy

    def __post_init__(self):
        """Check the type of the attributes and log or raise an error if the types don't match."""
        for attr_name, attr_type in self.__annotations__.items():
            attr_value = getattr(self, attr_name)
            if not isinstance(attr_value, attr_type):
                raise TypeError(
                    f"Attribute '{attr_name}' is expected to be of type {attr_type}, but got {type(attr_value)} instead."
                )


class IOParser:
    __organization = {
        "actions": ["control_policy"],
        "disturbance": ["distribution_name","disturbance_parameters"],
        "stochastic_dynamical_system": ["state_space_dimension","control_space_dimension","disturbance_space_dimension","dynamics"],
        "synthesis_config": ["maximal_polynomial_degree","epsilon","probability_threshold","theorem_name","solver_name"],
        "specification": ["ltl_formula","predicate_lookup"],
    }

    def __init__(self, *input_files: str):
        if not input_files:
            raise ValueError("At least one input file must be provided.")
        self.input_files = input_files

    @staticmethod
    def _parse_json(*file_path: str) -> dict:
        _structure = {}
        for file in file_path:
            logger.info(f"Parsing JSON file: {file}")
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
        logger.info(f"All the provided JSON files parsed successfully.")
        return _structure

    @staticmethod
    def _parse_yaml(*file_path: str) -> dict:
        _structure = {}
        for file in file_path:
            logger.info(f"Parsing YAML file: {file}")
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
        logger.info(f"All the provided YAML files parsed successfully.")
        return _structure

    @staticmethod
    def process_dict_to_tool_input(data: dict) -> ToolInput:
        _poly_max_ever = data["synthesis_config"]["maximal_polynomial_degree"]
        action_max_deg = data["actions"].get("maximal_polynomial_degree", _poly_max_ever) if "actions" in data else _poly_max_ever
        actions = {
            "action_dimension": data["stochastic_dynamical_system"]["control_space_dimension"],
            "state_dimension": data["stochastic_dynamical_system"]["state_space_dimension"],
            "maximal_degree": action_max_deg,
            "policies": data["actions"].get("control_policy", None) if "actions" in data else None,
            "limits": {
                "min": data.get("actions", {}).get("minimum", None),
                "max": data.get("actions", {}).get("maximum", None),
            }
        }

        disturbance = {
            "dimension": data["stochastic_dynamical_system"]["disturbance_space_dimension"],
            "distribution_name": data["disturbance"]["distribution_name"],
            "distribution_generator_parameters": data["disturbance"]["disturbance_parameters"],
        }

        _system_dynamic_equations = [
            ConditionalDynamics(
                condition=extract_space_inequalities(item["condition"]),
                dynamics=[Equation.extract_equation_from_string(eq) for eq in item["transforms"]]
            )
            for item in data["stochastic_dynamical_system"]["dynamics"]
        ]
        system_dynamic = {
            "state_dimension": data["stochastic_dynamical_system"]["state_space_dimension"],
            "action_dimension": data["stochastic_dynamical_system"]["control_space_dimension"],
            "disturbance_dimension": data["stochastic_dynamical_system"]["disturbance_space_dimension"],
            "system_transformations": _system_dynamic_equations
        }

        synthesis_config = {
            "maximal_polynomial_degree": data["synthesis_config"]["maximal_polynomial_degree"],
            "probability_threshold": data["synthesis_config"]["probability_threshold"],
            "theorem_name": data["synthesis_config"]["theorem_name"],
            "solver_name": data["synthesis_config"]["solver_name"],
            "owl_path": data["synthesis_config"]["owl_path"],
        }

        specification = {
            "ltl_formula": data["specification"].get("ltl_formula", None),
            "predicate_lookup": data["specification"].get("preposition_lookup", {}),
            "owl_binary_path": data["synthesis_config"].get("owl_path", None),
            "hoa_path": data["specification"].get("hoa_path", None),
        }

        return ToolInput(
            actions_pre=actions,
            disturbance_pre=disturbance,
            sds_pre=system_dynamic,
            synthesis_config_pre=synthesis_config,
            specification_pre=specification,
            system_space_pre=data["stochastic_dynamical_system"]["system_space"],
            initial_space_pre=data["stochastic_dynamical_system"]["initial_space"],
            enable_linear_invariants=data["synthesis_config"].get("use_linear_invariant", False)
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
        return self.process_dict_to_tool_input(_structure)


