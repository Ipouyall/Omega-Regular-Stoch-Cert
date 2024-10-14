import glob
import os.path
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Dict, Callable

from . import logger
from .action import SystemDecomposedControlPolicy
from .automata.graph import Automata
from .automata.hoaParser import HOAParser
from .automata.specification import LDBASpecification
from .config import SynthesisConfig
from .dynamics import SystemDynamics
from .noise import SystemStochasticNoise
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
    Done = 4

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
            RunningStage.POLICY_PREPARATION: self._run_stage_policy_preparation
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
            print("- Directory detected. Parsing all files in the directory.")
            files = glob.glob(os.path.join(self.input_path, "*.yaml")) + glob.glob(os.path.join(self.input_path, "*.json")) + glob.glob(os.path.join(self.input_path, "*.yml"))
            logger.info(f"Provided a directory. {len(files)} files found in {self.input_path}")
        elif os.path.isfile(self.input_path):
            files = [self.input_path]
            logger.info(f"Provided a file. {self.input_path} will be parsed.")
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
        sds = SystemDynamics(**self.history["initiator"].sds_pre)
        print("+ Constructed 'Stochastic Dynamical System' successfully.")

        ltl_specification = LDBASpecification(**self.history["initiator"].specification_pre)
        ldba_hoa = ltl_specification.get_HOA(os.path.join(self.output_path, "ltl2ldba.hoa"))
        print("+ Retrieved 'LDBA HOA' successfully.")

        hoa_parser = HOAParser()
        automata = hoa_parser(ldba_hoa)

        ldba = Automata.from_hoa(
            hoa_header=automata["header"],
            hoa_states=automata["states"]
        )
        print("+ Constructed 'LDBA' successfully.")

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
        print("+", policy)


