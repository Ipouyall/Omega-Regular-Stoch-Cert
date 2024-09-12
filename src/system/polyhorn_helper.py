import json

from .certificate.RASM import ReachAvoidSuperMartingaleCertificate
from .toolIO import ToolInput

from polyhorn.main import execute


class CommunicationBridge:

    __constant_definition_template = "(declare-const {const_name} Real)"
    __check_sat_template = "(check-sat)"
    __get_model_template = "(get-model)"

    @staticmethod
    def get_input_string(tool_io: ToolInput, certificate: ReachAvoidSuperMartingaleCertificate) -> str:
        constants = certificate.get_generated_constants()
        constants.update(tool_io.action_policy.get_generated_constants())
        constants = "\n".join([CommunicationBridge.__constant_definition_template.format(const_name=const) for const in constants])

        constraints = certificate.get_constraints()
        constraints = "\n".join([constraint.to_polyhorn_preorder() for constraint in constraints])

        return f"{constants}\n\n{constraints}\n\n{CommunicationBridge.__check_sat_template}\n{CommunicationBridge.__get_model_template}"

    @staticmethod
    def get_input_config(tool_io: ToolInput) -> str:
        config_template = {
            "theorem_name": tool_io.synthesis_config.theorem_name,
            "degree_of_sat": tool_io.synthesis_config.maximal_polynomial_degree,
            "degree_of_nonstrict_unsat": 0,
            "degree_of_strict_unsat": 0,
            "max_d_of_strict": 0,
            "solver_name": tool_io.synthesis_config.solver_name,
            "output_path": "temporary_polyhorn_result.txt",
            "unsat_core_heuristic": False,
            "SAT_heuristic": False,
            "integer_arithmetic": False
        }
        return json.dumps(config_template, indent=4)

    @staticmethod
    def feed_to_polyhorn(config, input_string):
        """
        https://github.com/ChatterjeeGroup-ISTA/PolyHorn
        """
        with open("temporary_polyhorn_config.json", "w") as f:
            f.write(config)
        with open("temporary_polyhorn_input.smt2", "w") as f:
            f.write(input_string)

        is_sat, model = execute(
            formula="temporary_polyhorn_input.smt2",
            config="temporary_polyhorn_config.json",
        )

        print(f"Is SAT: {is_sat}")
        print(f"Model: {model}")