import glob
import os.path
import sys
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Dict, Callable

from tqdm import tqdm

from . import logger
from .action import SystemDecomposedControlPolicy
from .automata.graph import Automata
from .automata.hoaParser import HOAParser
from .automata.specification import LDBASpecification
from .automata.visualize import visualize_automata
from .certificate.cl_constraint import ControllerBounds
from .certificate.init_constraints import InitialSpaceConstraint
from .certificate.nn_constraint import NonNegativityConstraint
from .certificate.nsed_constraints import NonStrictExpectedDecrease
from .certificate.sed_constraints import StrictExpectedDecrease
from .certificate.template import LTLCertificateDecomposedTemplates
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
        self.pbar.write(f"{BOLD}{self.running_stage}{RESET} Stage started...")

        # st = time.perf_counter()
        result = func(self, *args, **kwargs)
        # du = time.perf_counter()  - st

        self.pbar.write(f"{BOLD}{SUCCESS}{self.running_stage}{RESET} Stage completed.")
        self.pbar.update(1)
        # self.pbar.set_postfix({"Spent": f"{du:.4f}s"})

        return result
    return wrapper


class RunningStage(Enum):
    PARSE_INPUT = 0
    PREPARE_REQUIREMENTS = 1
    CONSTRUCT_SYSTEM_STATES = 2
    POLICY_PREPARATION = 3
    SYNTHESIZE_TEMPLATE = 4
    GENERATE_CONSTRAINTS = 5
    PREPARE_SOLVER_INPUTS = 6
    RUN_SOLVER = 7
    Done = 8

    def next(self):
        return RunningStage((self.value + 1) % len(RunningStage))

    def __str__(self):
        return f"[{self.value:<1}-{self.name.replace('_', ' ').title()}]"



@dataclass
class Runner:
    input_path: str
    output_path: str
    running_stage: RunningStage = field(init=False, default=RunningStage.PARSE_INPUT)
    history: dict = field(init=False, default_factory=dict)
    pbar: tqdm = field(init=False, default=None)

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
            RunningStage.SYNTHESIZE_TEMPLATE: self._run_template_synthesis,
            RunningStage.GENERATE_CONSTRAINTS: self._run_stage_generate_constraints,
            RunningStage.PREPARE_SOLVER_INPUTS: self._run_stage_prepare_solver_inputs,
            RunningStage.RUN_SOLVER: self._run_solver,
        }
        self.pbar = tqdm(
            range(RunningStage.Done.value),
            file=sys.stdout,
            colour="cyan",
            leave=True,
        )

    def run(self):
        while self.running_stage != RunningStage.Done:
            stage_runner = self.stage_runners.get(self.running_stage)
            if stage_runner is None:
                raise ValueError(f"Unknown stage: {self.running_stage}")
            stage_runner()
            self.running_stage = self.running_stage.next()
        self.pbar.close()

    @stage_logger
    def _run_stage_parsing(self):
        if os.path.isdir(self.input_path):
            self.pbar.write("+ Directory detected. Parsing all files in the directory.")
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
        self.pbar.write("+ Constructed 'System Space' successfully.")

        initial_space = SystemSpace(space_inequalities=self.history["initiator"].initial_space_pre)
        self.pbar.write("+ Constructed 'Initial Space' successfully.")

        sds = SystemDynamics(**self.history["initiator"].sds_pre)
        self.pbar.write("+ Constructed 'Stochastic Dynamical System' successfully.")

        ltl_specification = LDBASpecification(**self.history["initiator"].specification_pre)
        ldba_hoa = ltl_specification.get_HOA(os.path.join(self.output_path, "ltl2ldba.hoa"))
        self.pbar.write("+ Retrieved 'LDBA HOA' successfully.")

        hoa_parser = HOAParser()
        automata = hoa_parser(ldba_hoa)

        ldba = Automata.from_hoa(
            hoa_header=automata["header"],
            hoa_states=automata["body"],
            lookup_table=self.history["initiator"].specification_pre["predicate_lookup"]
        )
        self.pbar.write("+ Constructed 'LDBA' successfully.")
        self.pbar.write(f"  + {ldba.to_detailed_string()}")

        self.history["space"] = system_space
        self.history["initial_space"] = initial_space
        self.history["sds"] = sds
        self.history["ltl2ldba"] = ldba_hoa
        self.history["ldba"] = ldba

    @stage_logger
    def _run_stage_policy_preparation(self):
        policy = SystemDecomposedControlPolicy(
            **self.history["initiator"].actions_pre,
            abstraction_dimension=len(self.history["ldba"].accepting_sink_sets_id)
        )
        self.history["control policy"] = policy
        self.pbar.write(f"  + {policy}")

    @stage_logger
    def _run_template_synthesis(self):
        template = LTLCertificateDecomposedTemplates(
            state_dimension=self.history["initiator"].sds_pre["state_dimension"],
            action_dimension=self.history["initiator"].sds_pre["action_dimension"],
            abstraction_dimension=len(self.history["ldba"].states),
            accepting_components_count=len(self.history["ldba"].accepting_sink_sets_id),
            maximal_polynomial_degree=self.history["initiator"].synthesis_config_pre["maximal_polynomial_degree"],
        )
        self.pbar.write("+ Synthesized 'Certificate Templates' successfully.")
        self.pbar.write(f"  + {template}")
        self.history["template"] = template

    @stage_logger
    def _run_stage_generate_constraints(self):
        initial_bound_generator = InitialSpaceConstraint(
            template_manager=self.history["template"],
            system_space=self.history["space"],
            initial_space=self.history["initial_space"],
            automata=self.history["ldba"],
        )
        initial_bound_constraints = initial_bound_generator.extract()
        self.pbar.write("+ Generated 'Initial Space Upper Bound Constraints' successfully.")
        for t in initial_bound_constraints:
            self.pbar.write(f"  + {t.to_detail_string()}")

        non_negativity_generator = NonNegativityConstraint(
            template_manager=self.history["template"],
            system_space=self.history["space"],
        )
        non_negativity_constraints = non_negativity_generator.extract()
        self.pbar.write("+ Generated 'Non-Negativity Constraints' successfully.")
        for t in non_negativity_constraints:
            self.pbar.write(f"  + {t.to_detail_string()}")

        strict_expected_decrease_generator = StrictExpectedDecrease(
            template_manager=self.history["template"],
            system_space=self.history["space"],
            decomposed_control_policy=self.history["control policy"],
            system_dynamics=self.history["sds"],
            disturbance=self.history["disturbance"],
            automata=self.history["ldba"],
            epsilon=self.history["synthesis"].epsilon,
            probability_threshold=self.history["synthesis"].probability_threshold
        )
        strict_expected_decrease_constraints = strict_expected_decrease_generator.extract()
        self.pbar.write("+ Generated 'Strict Expected Decrease Constraints' successfully.")
        for t in strict_expected_decrease_constraints:
            self.pbar.write(f"  + {t.to_detail_string()}")

        non_strict_expected_decrease_generator = NonStrictExpectedDecrease(
            template_manager=self.history["template"],
            system_space=self.history["space"],
            decomposed_control_policy=self.history["control policy"],
            system_dynamics=self.history["sds"],
            disturbance=self.history["disturbance"],
            automata=self.history["ldba"],
            epsilon=self.history["synthesis"].epsilon,
            probability_threshold=self.history["synthesis"].probability_threshold
        )
        non_strict_expected_decrease_constraints = non_strict_expected_decrease_generator.extract()
        self.pbar.write("+ Generated 'Non-Strict Expected Decrease Constraints' successfully.")
        for t in non_strict_expected_decrease_constraints:
            self.pbar.write(f"  + {t.to_detail_string()}")

        controller_boundary_generator = ControllerBounds(
            template_manager=self.history["template"],
            system_space=self.history["space"],
            decomposed_control_policy=self.history["control policy"]
        )
        controller_bound_constraints = controller_boundary_generator.extract()
        if len(controller_bound_constraints) > 0:
            self.pbar.write("+ Generated 'Controller Boundary Constraints' successfully.")
            for t in controller_bound_constraints:
                self.pbar.write(f"  + {t.to_detail_string()}")

        self.history["constraints"] = {
            "initial_bound": initial_bound_constraints,
            "non_negativity": non_negativity_constraints,
            "strict_expected_decrease": strict_expected_decrease_constraints,
            "non_strict_expected_decrease": non_strict_expected_decrease_constraints,
            "controller_bound": controller_bound_constraints,
        }

    @stage_logger
    def _run_stage_prepare_solver_inputs(self):
        constants = self.history["control policy"].get_generated_constants() | self.history["template"].get_generated_constants()
        polyhorn_input = CommunicationBridge.get_input_string(
            generated_constants=constants,
            **self.history["constraints"]
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
        self.pbar.write("+ Polyhorn solver completed.")
        self.pbar.write(f"  + Satisfiability: {result['is_sat']}")
        self.pbar.write(f"    Model:")
        for k in sorted(result["model"].keys()):
            self.pbar.write(f"           {k}: {result["model"][k]}")
        self.history["solver_result"] = result
