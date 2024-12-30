import json
import os.path
from .certificate.constraint_inequality import ConstraintInequality

from polyhorn.main import execute


class CommunicationBridge:

    __constant_definition_template = "(declare-const {const_name} Real)"
    __check_sat_template = "(check-sat)"
    __get_model_template = "(get-model)"

    @staticmethod
    def get_input_string(generated_constants: set[str], **certificate: list[ConstraintInequality]) -> str:
        constants = "\n".join(
            CommunicationBridge.__constant_definition_template.format(const_name=const)
            for const in generated_constants
        )

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
            "output_path": os.path.abspath(os.path.join(synthesis_config["output_path"], "poly_horn_temp.txt")),
            "unsat_core_heuristic": True,
            "SAT_heuristic": True,
            "integer_arithmetic": False
        }
        return json.dumps(config_template, indent=4)

    @staticmethod
    def dump_polyhorn_input(input_string, config, temp_dir):
        config_path = os.path.join(temp_dir, "temporary_polyhorn_config.json")
        input_path = os.path.join(temp_dir, "temporary_polyhorn_input.smt2")
        with open(config_path, "w") as f:
            f.write(config)
        with open(input_path, "w") as f:
            f.write(input_string)

    @staticmethod
    def feed_to_polyhorn(temp_dir, timeout=0.1*60):
        """
        https://github.com/ChatterjeeGroup-ISTA/PolyHorn
        """
        config_path = os.path.join(temp_dir, "temporary_polyhorn_config.json")
        input_path = os.path.join(temp_dir, "temporary_polyhorn_input.smt2")

        is_sat, model = execute(
            formula=input_path,
            config=config_path,
        )

        print("Polyhorn failed to execute.")
        return {"is_sat": is_sat,"model": model}
