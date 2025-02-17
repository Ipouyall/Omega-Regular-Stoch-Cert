import glob
import os.path
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Dict, Callable

from .log import logger
from .action import SystemDecomposedControlPolicy
from .automata.graph import Automata
from .automata.hoaParser import HOAParser
from .automata.synthesis import LDBASpecification
from .certificate.beiC import BoundedExpectedIncreaseConstraint
from .certificate.cbC import ControllerBounds
from .certificate.initialC import InitialSpaceConstraint
from .certificate.invariant.initial_constraint import InvariantInitialConstraint
from .certificate.invariant.inductive_constraint import InvariantInductiveConstraint
from .certificate.invariant.template import InvariantTemplate, InvariantFakeTemplate
from .certificate.nnC import NonNegativityConstraint
from .certificate.safeC import SafetyConstraint
from .certificate.safety_condition import SafetyConditionHandler
from .certificate.sedC import StrictExpectedDecreaseConstraint
from .certificate.template import LTLCertificateDecomposedTemplates, CertificateVariables
from .certificate.variableC import TemplateVariablesConstraint
from .config import SynthesisConfig
from .dynamics import SystemDynamics
from .noise import SystemStochasticNoise
from .polyhorn_helper import CommunicationBridge
from .space import SystemSpace
from .toolIO import IOParser

BOLD = "\033[1m"
WARNING = "\033[33m"
SUCCESS = "\033[32m"
ERROR = "\033[31m"
RESET = "\033[0m"


def stage_logger(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        print(f"{BOLD}{self.running_stage}{RESET} Stage started...")
        result = func(self, *args, **kwargs)
        print(f"{BOLD}{SUCCESS}{self.running_stage}{RESET} Stage completed.")
        return result
    return wrapper


class RunningStage(Enum):
    PARSE_INPUT = 0
    PREPARE_REQUIREMENTS = 1
    CONSTRUCT_SYSTEM_STATES = 2
    POLICY_PREPARATION = 3
    SYNTHESIZE_INVARIANTS = 4
    SYNTHESIZE_TEMPLATE = 5
    GENERATE_CONSTRAINTS = 6
    PREPARE_SOLVER_INPUTS = 7
    RUN_SOLVER = 8
    Done = 9

    def next(self):
        return RunningStage((self.value + 1) % len(RunningStage))

    def __str__(self):
        return f"[{self.value:<1}-{self.name.replace('_', ' ').title()}]"


def fix_model_output(model: dict, automata: Automata):
    policy_acc = {}
    policy_buchi = {}
    refined_model = {}
    buchi_sig = "Pb0_"
    acc_sig = "Pa_"

    get_last_digit = lambda x: int(x.split("_")[-1])
    get_fixed_component = lambda sig, partial: {f"{sig}_{k}": v for k, v in partial.items()}

    for k, v in model.items():
        if k.startswith(buchi_sig):
            policy_buchi[get_last_digit(k)] = v
        elif k.startswith(acc_sig):
            policy_acc[get_last_digit(k)] = v
        else:
            refined_model[k] = v

    if len(policy_acc) == 0 or len(policy_buchi) == 0:
        return refined_model

    for st in automata.states:
        if st.is_accepting():
            for k, v in get_fixed_component(f"P_{st.state_id}", policy_acc).items():
                refined_model[k] = v
        else:
            for k, v in get_fixed_component(f"P_{st.state_id}", policy_buchi).items():
                refined_model[k] = v
    return refined_model


@dataclass
class Runner:
    input_path: str
    output_path: str
    running_stage: RunningStage = field(init=False, default=RunningStage.PARSE_INPUT)
    history: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        if not self.output_path:
            _base = os.path.dirname(self.input_path) if not os.path.isdir(self.input_path) else self.input_path
            self.output_path = os.path.join(_base, "temp")
            logger.warning(f"Output path not provided. Using default path: {self.output_path}")
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        self.stage_runners: Dict[RunningStage, Callable] = {
            RunningStage.PARSE_INPUT: self._run_stage_parsing,
            RunningStage.PREPARE_REQUIREMENTS: self._run_stage_prepare_req,
            RunningStage.CONSTRUCT_SYSTEM_STATES: self._run_stage_state_construction,
            RunningStage.POLICY_PREPARATION: self._run_stage_policy_preparation,
            RunningStage.SYNTHESIZE_INVARIANTS: self._run_stage_synthesize_invariants,
            RunningStage.SYNTHESIZE_TEMPLATE: self._run_template_synthesis,
            RunningStage.GENERATE_CONSTRAINTS: self._run_stage_generate_constraints,
            RunningStage.PREPARE_SOLVER_INPUTS: self._run_stage_prepare_solver_inputs,
            RunningStage.RUN_SOLVER: self._run_solver,
        }

    def run(self):
        while self.running_stage != RunningStage.Done:
            stage_runner = self.stage_runners.get(self.running_stage)
            if stage_runner is None:
                raise ValueError(f"Unknown stage: {self.running_stage}")
            stage_runner()
            self.running_stage = self.running_stage.next()

    @stage_logger
    def _run_stage_parsing(self):
        if os.path.isdir(self.input_path):
            print("+ Directory detected. Parsing all files in the directory.")
            files = glob.glob(os.path.join(self.input_path, "*.yaml")) + glob.glob(os.path.join(self.input_path, "*.json")) + glob.glob(os.path.join(self.input_path, "*.yml"))
            logger.info(f"  + Provided a directory. {len(files)} files found in {self.input_path}")
        elif os.path.isfile(self.input_path):
            files = [self.input_path]
            logger.info(f"+ Provided a file. {self.input_path} will be parsed.")
        else:
            raise FileNotFoundError(f"Input path not found: {self.input_path}")

        parser = IOParser(self.output_path, *files)
        input_pre = parser.parse()

        self.history["initiator"] = input_pre

    @stage_logger
    def _run_stage_prepare_req(self):
        disturbance = SystemStochasticNoise(**self.history["initiator"].disturbance_pre)
        self.history["disturbance"] = disturbance

        synthesis = SynthesisConfig(**self.history["initiator"].synthesis_config_pre)
        self.history["synthesis"] = synthesis

    @stage_logger
    def _run_stage_state_construction(self):
        system_space = SystemSpace(space_inequalities=self.history["initiator"].system_space_pre)
        print("+ Constructed 'System Space' successfully.")

        initial_space = SystemSpace(space_inequalities=self.history["initiator"].initial_space_pre)
        print("+ Constructed 'Initial Space' successfully.")

        sds = SystemDynamics(**self.history["initiator"].sds_pre)
        print("+ Constructed 'Stochastic Dynamical System' successfully.")

        ltl_specification = LDBASpecification(**self.history["initiator"].specification_pre)
        ldba_hoa = ltl_specification.get_HOA(os.path.join(self.output_path, "ltl2ldba.hoa"))
        print("+ Retrieved 'LDBA HOA' successfully.")

        hoa_parser = HOAParser()
        automata = hoa_parser(ldba_hoa)

        ldba = Automata.from_hoa(
            hoa_header=automata["header"],
            hoa_states=automata["body"],
            lookup_table=self.history["initiator"].specification_pre["predicate_lookup"]
        )
        print("+ Constructed 'LDBA' successfully.")
        print(f"  + {ldba.to_detailed_string()}")

        self.history["space"] = system_space
        self.history["initial_space"] = initial_space
        self.history["sds"] = sds
        self.history["ltl2ldba"] = ldba_hoa
        self.history["ldba"] = ldba

    @stage_logger
    def _run_stage_policy_preparation(self):
        policy = SystemDecomposedControlPolicy(
            **self.history["initiator"].actions_pre,
            abstraction_dimension=len(self.history["ldba"].accepting_component_ids)
        )
        self.history["control policy"] = policy
        print(f"  + {policy}")

    @stage_logger
    def _run_stage_synthesize_invariants(self):
        if not self.history["initiator"].enable_linear_invariants:
            inv_template = InvariantFakeTemplate()
            print("+ Synthesizing 'Invariant Template' skipped.")
            self.history["invariant template"] = inv_template
            return

        inv_template = InvariantTemplate(
            state_dimension=self.history["initiator"].sds_pre["state_dimension"],
            action_dimension=self.history["initiator"].sds_pre["action_dimension"],
            abstraction_dimension=len(self.history["ldba"].states),
            maximal_polynomial_degree=self.history["initiator"].synthesis_config_pre["maximal_polynomial_degree"],
        )
        print("+ Synthesized 'Invariant Template' successfully.")
        print(f"  + {inv_template}")
        self.history["invariant template"] = inv_template

        inv_init_constraint_gen = InvariantInitialConstraint(
            template=inv_template,
            system_space=self.history["space"],
            initial_space=self.history["initial_space"],
            automata=self.history["ldba"],
        )
        inv_init_constraint = inv_init_constraint_gen.extract()
        print("+ Generated Invariant's 'Initial Constraint' successfully.")
        # for t in inv_init_constraint:
        #     print(f"  + {t.to_detail_string()}")

        inv_inductive_constraint_gen = InvariantInductiveConstraint(
            template=inv_template,
            system_space=self.history["space"],
            decomposed_control_policy=self.history["control policy"],
            disturbance=self.history["disturbance"],
            system_dynamics=self.history["sds"],
            automata=self.history["ldba"],
        )
        inv_inductive_constraint = inv_inductive_constraint_gen.extract()
        print("+ Generated Invariant's 'Inductive Constraint' successfully.")
        # for t in inv_inductive_constraint:
        #     print(f"  + {t.to_detail_string()}")

        self.history["invariant_constraints"] = {
            "invariant_initial": inv_init_constraint,
            "invariant_inductive": inv_inductive_constraint,
        }

    @stage_logger
    def _run_template_synthesis(self):
        certificate_variables = CertificateVariables(
            probability_threshold=self.history["initiator"].synthesis_config_pre["probability_threshold"],
            delta_safe=1,
        )
        template = LTLCertificateDecomposedTemplates(
            state_dimension=self.history["initiator"].sds_pre["state_dimension"],
            action_dimension=self.history["initiator"].sds_pre["action_dimension"],
            abstraction_dimension=len(self.history["ldba"].states),
            accepting_components_count=len(self.history["ldba"].accepting_component_ids),
            maximal_polynomial_degree=self.history["initiator"].synthesis_config_pre["maximal_polynomial_degree"],
            variables=certificate_variables
        )
        print("+ Synthesized 'Certificate Templates' successfully.")
        print(f"  + {template}")
        self.history["template"] = template

    @stage_logger
    def _run_stage_generate_constraints(self):
        initial_space_generator = InitialSpaceConstraint(
            template_manager=self.history["template"],
            system_space=self.history["space"],
            initial_space=self.history["initial_space"],
            automata=self.history["ldba"],
        )
        initial_space_constraints = initial_space_generator.extract()
        print("+ Generated 'Initial Space Upper Bound Constraints' successfully.")
        # for t in initial_space_constraints:
        #     print(f"  + {t.to_detail_string()}")

        safety_generator = SafetyConstraint(
            template_manager=self.history["template"],
            invariant=self.history["invariant template"],
            system_space=self.history["space"],
            automata=self.history["ldba"],
        )
        safety_constraints = safety_generator.extract()
        print("+ Generated 'Safety Constraints' successfully.")
        # for t in safety_constraints:
        #     print(f"  + {t.to_detail_string()}")

        non_negativity_generator = NonNegativityConstraint(
            template_manager=self.history["template"],
            invariant=self.history["invariant template"],
            system_space=self.history["space"],
        )
        non_negativity_constraints = non_negativity_generator.extract()
        print("+ Generated 'Non-Negativity Constraints' successfully.")
        # for t in non_negativity_constraints:
        #     print(f"  + {t.to_detail_string()}")

        safety_condition_handler = SafetyConditionHandler(
            template_manager=self.history["template"],
            decomposed_control_policy=self.history["control policy"],
            disturbance=self.history["disturbance"],
            automata=self.history["ldba"],
        )

        strict_expected_decrease_generator = StrictExpectedDecreaseConstraint(
            template_manager=self.history["template"],
            invariant=self.history["invariant template"],
            system_space=self.history["space"],
            decomposed_control_policy=self.history["control policy"],
            disturbance=self.history["disturbance"],
            system_dynamics=self.history["sds"],
            automata=self.history["ldba"],
            safety_condition_handler=safety_condition_handler
        )
        strict_expected_decrease_constraints = strict_expected_decrease_generator.extract()
        print("+ Generated 'Strict Expected Decrease Constraints' successfully.")
        # for t in strict_expected_decrease_constraints:
        #     print(f"  + {t.to_detail_string()}")

        bounded_expected_increase_generator = BoundedExpectedIncreaseConstraint(
            template_manager=self.history["template"],
            invariant=self.history["invariant template"],
            system_space=self.history["space"],
            decomposed_control_policy=self.history["control policy"],
            disturbance=self.history["disturbance"],
            system_dynamics=self.history["sds"],
            automata=self.history["ldba"],
            safety_condition_handler=safety_condition_handler
        )
        bounded_expected_increase_constraints = bounded_expected_increase_generator.extract()
        print("+ Generated 'Bounded Expected Increase Constraints' successfully.")
        # for t in bounded_expected_increase_constraints:
        #     print(f"  + {t.to_detail_string()}")

        controller_boundary_generator = ControllerBounds(
            template_manager=self.history["template"],
            system_space=self.history["space"],
            decomposed_control_policy=self.history["control policy"]
        )
        controller_bound_constraints = controller_boundary_generator.extract()
        if len(controller_bound_constraints) > 0:
            print("+ Generated 'Controller Boundary Constraints' successfully.")
            # for t in controller_bound_constraints:
            #     print(f"  + {t.to_detail_string()}")

        variables_gen = TemplateVariablesConstraint(
            template_manager=self.history["template"]
        )
        variables_constraints = variables_gen.extract()
        if len(variables_constraints) > 0:
            print("+ Generated 'Template Variables Constraints' successfully.")
            # for t in variables_constraints:
            #     print(f"  + {t.to_detail_string()}")

        self.history["constraints"] = {
            "template_variables": variables_constraints,
            "initial_space": initial_space_constraints,
            "non_negativity": non_negativity_constraints,
            "safety": safety_constraints,
            "strict_expected_decrease": strict_expected_decrease_constraints,
            "bounded_expected_increase": bounded_expected_increase_constraints,
            "controller_bound": controller_bound_constraints,
        }

    @stage_logger
    def _run_stage_prepare_solver_inputs(self):
        constants = self.history["control policy"].get_generated_constants() | self.history["template"].get_generated_constants() | self.history["invariant template"].get_generated_constants()

        print(f"+ Constraints passed to the solver:")
        for k, v in self.history["constraints"].items():
            print(f"  + {k}: {len(v)}x")

        print(f"+ Number of constants: {len(constants)}")
        print(f"  + From Control Policy: {len(self.history['control policy'].get_generated_constants())}")
        print(f"  + From Certificate Template: {len(self.history['template'].get_generated_constants())}")
        print(f"  + From Invariant Template: {len(self.history['invariant template'].get_generated_constants())}")

        polyhorn_input = CommunicationBridge.get_input_string(
            generated_constants=constants,
            **self.history.get("invariant_constraints", {}),
            **self.history["constraints"],
        )
        polyhorn_config = CommunicationBridge.get_input_config(
            **self.history["initiator"].synthesis_config_pre,
            output_path=self.output_path
        )
        CommunicationBridge.dump_polyhorn_input(
            input_string=polyhorn_input,
            config=polyhorn_config,
            temp_dir=self.output_path
        )

    @stage_logger
    def _run_solver(self):
        result = CommunicationBridge.feed_to_polyhorn(self.output_path)
        print("+ Polyhorn solver completed.")
        print(f"  + Satisfiability: {result['is_sat']}")
        print(f"    Model:")
        result["model"] = fix_model_output(result["model"], self.history["ldba"])
        for k in sorted(result["model"].keys()):
            print(f"           {k}: {result["model"][k]}")
        self.history["solver_result"] = result
