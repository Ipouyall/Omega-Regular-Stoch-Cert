import json
import os.path

from .action import SystemDecomposedControlPolicy
from .certificate.constraint_inequality import ConstraintInequality

from polyhorn.main import execute


class CommunicationBridge:

    __constant_definition_template = "(declare-const {const_name} Real)"
    __check_sat_template = "(check-sat)"
    __get_model_template = "(get-model)"

    @staticmethod
    def get_input_string(policy: SystemDecomposedControlPolicy, **certificate: list[ConstraintInequality]) -> str:
        constants = policy.get_generated_constants()
        constants = "\n".join([CommunicationBridge.__constant_definition_template.format(const_name=const) for const in constants])

        constraints = "\n".join([
            constraint.to_polyhorn_preorder()
            for constraints in certificate.values()
            for constraint in constraints
        ])

        return f"{constants}\n\n{constraints}\n\n{CommunicationBridge.__check_sat_template}\n{CommunicationBridge.__get_model_template}"

    @staticmethod
    def get_input_config(**synthesis_config) -> str:
        """
        It looks for the following keys: "theorem_name", "maximal_polynomial_degree", "solver_name", "output_path"
        """
        config_template = {
            "theorem_name": synthesis_config["theorem_name"],
            "degree_of_sat": synthesis_config["maximal_polynomial_degree"],
            "degree_of_nonstrict_unsat": 0,
            "degree_of_strict_unsat": 0,
            "max_d_of_strict": 0,
            "solver_name": synthesis_config["solver_name"],
            "output_path": os.path.abspath(synthesis_config["output_path"]),
            "unsat_core_heuristic": False,
            "SAT_heuristic": False,
            "integer_arithmetic": False
        }
        return json.dumps(config_template, indent=4)

    @staticmethod
    def dump_polyhorn_input(input_string, config, temp_dir):
        config_path = f"{temp_dir}_temporary_polyhorn_config.json"
        input_path = f"{temp_dir}_temporary_polyhorn_input.smt2"
        with open(config_path, "w") as f:
            f.write(config)
        with open(input_path, "w") as f:
            f.write(input_string)

    @staticmethod
    def feed_to_polyhorn(temp_dir):
        """
        https://github.com/ChatterjeeGroup-ISTA/PolyHorn
        """
        config_path = f"{temp_dir}_temporary_polyhorn_config.json"
        input_path = f"{temp_dir}_temporary_polyhorn_input.smt2"

        is_sat, model = execute(
            formula=input_path,
            config=config_path,
        )

        return {
            "is_sat": is_sat,
            "model": model
        }
