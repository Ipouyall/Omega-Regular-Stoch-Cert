import os.path
import time
from enum import Enum
from functools import wraps

import pandas as pd
import streamlit as st
from dataclasses import dataclass, field

from streamlit_option_menu import option_menu

from .configure import Configuration
from .plotter import plot_dynamics_from_conditional_eq
from .upload import upload_file
from ..action import SystemDecomposedControlPolicy
from ..automata.graph import Automata
from ..automata.hoaParser import HOAParser
from ..automata.synthesis import LDBASpecification
from ..automata.visualize import visualize_automata
from ..certificate.init_constraints import InitialSpaceConstraint
from ..certificate.nn_constraint import NonNegativityConstraint
from ..certificate.nsed_constraints import NonStrictExpectedDecrease
from ..certificate.strict_expected_decrease import StrictExpectedDecrease
from ..certificate.template import LTLCertificateDecomposedTemplates
from ..config import SynthesisConfig
from ..dynamics import SystemDynamics
from ..noise import SystemStochasticNoise
from ..polyhorn_helper import CommunicationBridge
from ..space import SystemSpace


class WebUIRunningStage(Enum):
    DIAGNOSE_CONFIG = 0
    CONSTRUCT_SYSTEM_PREREQUIREMENT = 1
    POLICY_PREPARATION = 2
    SYNTHESIZE_TEMPLATE = 3
    GENERATE_CONSTRAINTS = 4
    PREPARE_SOLVER_INPUTS = 5
    RUN_SOLVER = 6
    CLEAN_TRASHES = 7

    def next(self):
        return WebUIRunningStage((self.value + 1) % len(WebUIRunningStage))


def ui_stage_logger(func):
    total_stages = len(WebUIRunningStage)
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.stage_desc.write(f"{self.running_stage.name.replace('_', ' ').title()} (running...)")
        self.pbar.progress(self.running_stage.value / total_stages)

        _st = time.perf_counter_ns()
        result = func(self, *args, **kwargs)
        _du = (time.perf_counter_ns() - _st) / 1e9

        self.stage_desc.write(f"{self.running_stage.name.replace('_', ' ').title()} (completed in {_du:.4f} seconds)")
        self.running_stage = self.running_stage.next()
        time.sleep(1.5)

        return result
    return wrapper

@dataclass
class WebUI:
    config: Configuration = field(default_factory=Configuration)
    running_stage: WebUIRunningStage = field(init=False, default=WebUIRunningStage.DIAGNOSE_CONFIG)
    history: dict = field(init=False, default_factory=dict)
    pbar: st.progress = field(init=False, default=None)
    temp_path: str = field(init=False, default="./temp_ltl_2025")

    def __post_init__(self):
        self.temp_path = os.path.abspath(self.temp_path)

    def _run_experiment(self, progress):
        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)
        progress_bar, stage_desc = progress.columns(2)
        self.stage_desc = stage_desc.empty()
        self.pbar = progress_bar.progress(0)
        self.running_stage = WebUIRunningStage.DIAGNOSE_CONFIG
        sub_functions = [
            self._run_experiment_diagnose_config,
            self._run_experiment_construct_system_states,
            self._run_experiment_policy_preparation,
            self._run_experiment_synthesize_template,
            self._run_experiment_generate_constraints,
            self._run_experiment_prepare_solver_inputs,
            self._run_experiment_run_solver,
            self._run_experiment_clean_trashes
        ]
        for func in sub_functions:
            func()

    @staticmethod
    def home_page():
        st.title("Welcome!")
        st.write("This is the home page of the application. You can navigate to other sections using the sidebar.")

    def upload_page(self):
        st.title("Upload your sample")
        st.write("Upload sample file(s). Please note that if you upload multiple files, they are considered as one sample and you are allowed to only run one sample at a time.")
        uploader = st.empty()
        col1, col2 = st.columns(2)
        status = col2.empty()
        uploaded_data = upload_file(status, uploader)
        update_data = col1.button(
            label="Update Configuration",
            help="Update the configuration with the uploaded data.",
            disabled=uploaded_data is None,
        )
        if update_data:
            self.config.update_from_data(uploaded_data)
            status.success("Configuration updated successfully!")
        if uploaded_data is not None:
            st.write('<span style="color: gray;"> Uploaded data preview</span>', unsafe_allow_html=True)
            st.json(uploaded_data, expanded=True)

    def run_page(self):
        st.title("Run the system")
        place_holder = st.empty()

        st.subheader('Experiment Configuration')
        col1, col2, col3 = st.columns(3)
        col1.write(f'System mode: <span style="color: gray;">{self.config.high_level_description.config_type.value}</span>', unsafe_allow_html=True)
        col2.write(f'State dimension: <span style="color: gray;">{self.config.high_level_description.state_dim}</span>', unsafe_allow_html=True)
        col3.write(f'Control dimension: <span style="color: gray;">{self.config.high_level_description.state_dim} → {self.config.high_level_description.control_dim}</span>', unsafe_allow_html=True)
        col1.write(f'Specification: <span style="color: gray;">{self.config.specification.get_formula()}</span>', unsafe_allow_html=True)
        col2.write(f'Theorem: <span style="color: gray;">{self.config.synthesis.theorem}</span>', unsafe_allow_html=True)
        col3.write(f'Solver maximum polynomial degree: <span style="color: gray;">{self.config.synthesis.max_degree}</span>', unsafe_allow_html=True)
        col1.write(f'Probability threshold: <span style="color: gray;">{self.config.synthesis.probability}</span>', unsafe_allow_html=True)
        col2.write(f'Epsilon: <span style="color: gray;">{self.config.synthesis.epsilon}</span>', unsafe_allow_html=True)

        start_experiment = col3.button(
            label="Start Experiment",
            help="Start the experiment with the current configuration.",
        )
        if start_experiment:
            self._run_experiment(progress=place_holder)
            place_holder.success("Experiment completed successfully!")

    def run(self):
        with st.sidebar:
            selected = option_menu(
                menu_title="Main Menu",
                options=["Home", "Upload a sample", "Manual configuration", "Run", "Documentation", "Contact Us"],
                icons=["house", "cloud-arrow-up-fill", "gear", "play", "book", "telephone-fill"],
                menu_icon="cast",
                default_index=0,
                orientation="vertical",
            )

        if selected == "Home":
            self.home_page()
        elif selected == "Upload a sample":
            self.upload_page()
        elif selected == "Manual configuration":
            self.config.view()
        elif selected == "Run":
            self.run_page()
        elif selected == "Documentation":
            st.error("This feature is not implemented yet.")
        elif selected == "Contact Us":
            st.error("This feature is not implemented yet.")

    @ui_stage_logger
    def _run_experiment_diagnose_config(self):
        self.initiator = self.config.get_tool_input()

    @ui_stage_logger
    def _run_experiment_construct_system_states(self):
        self.disturbance = SystemStochasticNoise(**self.initiator.disturbance_pre)
        self.synthesis = SynthesisConfig(**self.initiator.synthesis_config_pre)
        self.space = SystemSpace(space_inequalities=self.initiator.system_space_pre)
        self.initial = SystemSpace(space_inequalities=self.initiator.initial_space_pre)

        self.sds = SystemDynamics(**self.initiator.sds_pre)
        with st.expander(f"Synthesized System Dynamics", expanded=False, icon="🔄"):
            plot_dynamics_from_conditional_eq(self.initiator.sds_pre["system_transformations"])

        ltl_specification = LDBASpecification(**self.initiator.specification_pre)
        self.hoa = ltl_specification.get_HOA(os.path.join(self.temp_path, "ltl2ldba.hoa"))
        hoa_parser = HOAParser()
        automata = hoa_parser(self.hoa)
        self.ldba = Automata.from_hoa(
            hoa_header=automata["header"],
            hoa_states=automata["states"],
            lookup_table=self.initiator.specification_pre["predicate_lookup"]
        )
        v_graph = visualize_automata(self.ldba)
        with st.expander(f"Synthesized Automata", expanded=False, icon="☁️"):
            st.graphviz_chart(v_graph)
            data = [{"Symbol": s, "Logic": p} for s, p in self.ldba.lookup_table.items()]
            data = pd.DataFrame(data)
            st.table(data)

    @ui_stage_logger
    def _run_experiment_policy_preparation(self):
        self.policy = SystemDecomposedControlPolicy(
            **self.initiator.actions_pre,
            abstraction_dimension=len(self.ldba.accepting_component_ids)
        )

    @ui_stage_logger
    def _run_experiment_synthesize_template(self):
        self.template = LTLCertificateDecomposedTemplates(
            state_dimension=self.initiator.sds_pre["state_dimension"],
            action_dimension=self.initiator.sds_pre["action_dimension"],
            abstraction_dimension=len(self.ldba.states),
            accepting_components_count=len(self.ldba.accepting_component_ids),
            maximal_polynomial_degree=self.initiator.synthesis_config_pre["maximal_polynomial_degree"],
        )

    @ui_stage_logger
    def _run_experiment_generate_constraints(self):
        initial_bound = InitialSpaceConstraint(
            template_manager=self.template,
            system_space=self.space,
            initial_space=self.initial,
            automata=self.ldba,
        ).extract()
        non_negativity = NonNegativityConstraint(
            template_manager=self.template,
            system_space=self.space,
        ).extract()
        strict_expected_decrease = StrictExpectedDecrease(
            template_manager=self.template,
            system_space=self.space,
            decomposed_control_policy=self.policy,
            system_dynamics=self.sds,
            disturbance=self.disturbance,
            automata=self.ldba,
            epsilon=self.synthesis.epsilon,
            probability_threshold=self.synthesis.probability_threshold
        ).extract()
        non_strict_expected_decrease = NonStrictExpectedDecrease(
            template_manager=self.template,
            system_space=self.space,
            decomposed_control_policy=self.policy,
            system_dynamics=self.sds,
            disturbance=self.disturbance,
            automata=self.ldba,
            epsilon=self.synthesis.epsilon,
            probability_threshold=self.synthesis.probability_threshold
        ).extract()
        self.constraints = {
            "initial_bound": initial_bound,
            "non_negativity": non_negativity,
            "strict_expected_decrease": strict_expected_decrease,
            "non_strict_expected_decrease": non_strict_expected_decrease,
        }

    @ui_stage_logger
    def _run_experiment_prepare_solver_inputs(self):
        constraints = self.policy.get_generated_constants() | self.template.get_generated_constants()
        polyhorn_input = CommunicationBridge.get_input_string(
            generated_constants=constraints,
            **self.constraints,
        )
        polyhorn_config = CommunicationBridge.get_input_config(
            **self.initiator.synthesis_config_pre,
            output_path=self.temp_path
        )
        CommunicationBridge.dump_polyhorn_input(
            input_string=polyhorn_input,
            config=polyhorn_config,
            temp_dir=self.temp_path
        )

    @ui_stage_logger
    def _run_experiment_run_solver(self):
        start_time = time.perf_counter()
        result = CommunicationBridge.feed_to_polyhorn(self.temp_path)
        duration = time.perf_counter() - start_time
        if result["is_sat"].lower() == "unsat":
            st.error("The provided specification is unsatisfiable.")
        elif result["is_sat"].lower() == "sat":
            st.success(f"The provided specification is satisfied in {duration:.3f} seconds.")
            st.json(result["model"], expanded=False)
        else:
            st.error("An error occurred while running the solver.")
            raise ValueError(f"Solver error: {result}")


    @ui_stage_logger
    def _run_experiment_clean_trashes(self):
        for file in os.listdir(self.temp_path):
            os.remove(os.path.join(self.temp_path, file))
        os.rmdir(self.temp_path)







