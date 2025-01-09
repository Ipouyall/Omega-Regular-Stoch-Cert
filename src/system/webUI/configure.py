import os
from enum import Enum

import streamlit as st
from dataclasses import dataclass, field

from ..dynamics import ConditionalDynamics
from ..polynomial.equation import Equation
from ..space import extract_space_inequalities
from ..toolIO import ToolInput

possible_atomic_propositions = {chr(i) for i in range(97, 123)}
possible_theorems = ["farkas", "handelman", "putinar"]
Possible_solvers = ["z3", "mathsat"]


class ConfigType(Enum):
    POLICY_SYNTHESIS = "Policy Synthesis"
    POLICY_VERIFICATION = "Policy Verification"
    SYSTEM_VERIFICATION = "System Verification"


@dataclass
class HighLevelDescription:
    config_type: ConfigType = ConfigType.POLICY_SYNTHESIS
    state_dim: int = 2
    control_dim: int = 1
    disturbance_dim: int = 1
    system_space: str = ""
    initial_space: str = ""


@dataclass
class Actions:
    max_degree: int = 2
    control_policy: list[str] = field(default_factory=list)


@dataclass
class Disturbance:
    name: str = "normal"
    parameters: dict[str, float] = field(default_factory=dict)

    def get_valid_distributions(self):
        return ['normal', 'uniform']

    def get_special_parameters(self):
        if self.name == "normal":
            return "mean", "std_dev"
        elif self.name == "uniform":
            return "lower_bound", "upper_bound"
        return NotImplemented

@dataclass
class SystemDefinition:
    dynamics: list[dict] = field(default_factory=list)


@dataclass
class Specification:
    formula: str = ""
    need_lookup_table: bool = False
    lookup_list: list = field(default_factory=list)
    lookup_table: dict = field(default_factory=dict)

    def get_formula(self):
        formula = self.formula
        if self.need_lookup_table:
            for key, value in self.lookup_table.items():
                formula = formula.replace(key, "'"+value+"'")
        return formula


@dataclass
class Synthesis:
    max_degree: int = 2
    epsilon: float = 1e-12
    probability: float = 0.9
    theorem: str = "farkas"
    solver: str = "z3"
    owl_path: str = "./owl"


def transformation_helper(label, default, key, no_action=False, no_disturbance=False, placeholder=None, help=""):
    if placeholder is None:
        new = st.text_input(
            label=label,
            value=default,
            key=key,
            help=help
        )
    else:
        new = placeholder.text_input(
            label=label,
            value=default,
            key=key,
            help=help
        )
    if no_action:
        if "A" in new:
            st.write(
                '<span style="color: #b16a6a;">Using control action in system verification is not available!</span>',
                unsafe_allow_html=True)
    if no_disturbance:
        if "D" in new:
            st.write('<span style="color: #b16a6a;">Using zero dimension disturbance is not available!</span>',
                     unsafe_allow_html=True)
    return new


@dataclass
class Configuration:
    high_level_description: HighLevelDescription = field(default_factory=HighLevelDescription)
    actions: Actions = field(default_factory=Actions)
    disturbance: Disturbance = field(default_factory=Disturbance)
    system_definition: SystemDefinition = field(default_factory=SystemDefinition)
    specification: Specification = field(default_factory=Specification)
    synthesis: Synthesis = field(default_factory=Synthesis)

    def update_from_data(self, data: dict):
        self.high_level_description.state_dim = data.get("stochastic_dynamical_system", {}).get("state_space_dimension", self.high_level_description.state_dim)
        self.high_level_description.control_dim = data.get("stochastic_dynamical_system", {}).get("control_space_dimension", self.high_level_description.control_dim)
        self.high_level_description.disturbance_dim = data.get("stochastic_dynamical_system", {}).get("disturbance_space_dimension", self.high_level_description.disturbance_dim)
        self.high_level_description.system_space = data.get("stochastic_dynamical_system", {}).get("system_space", self.high_level_description.system_space)
        self.high_level_description.initial_space = data.get("stochastic_dynamical_system", {}).get("initial_space", self.high_level_description.initial_space)

        if "maximal_polynomial_degree" in data.get("actions", {}):
            self.actions.max_degree = data["actions"]["maximal_polynomial_degree"]
        self.actions.max_degree = data.get("synthesis_config", {}).get("maximal_polynomial_degree", self.actions.max_degree)
        self.actions.control_policy = data.get("actions", {}).get("control_policy", self.actions.control_policy)

        self.disturbance.name = data.get("disturbance", {}).get("distribution_name", self.disturbance.name)
        self.disturbance.parameters = data.get("disturbance", {}).get("disturbance_parameters", self.disturbance.parameters)

        self.system_definition.dynamics = data.get("stochastic_dynamical_system", {}).get("dynamics", self.system_definition.dynamics)

        self.specification.formula = data.get("specification", {}).get("ltl_formula", self.specification.formula)
        if "preposition_lookup" in data.get("specification", {}):
            self.specification.need_lookup_table = True
            self.specification.lookup_list = list(data["specification"]["preposition_lookup"].keys())
            self.specification.lookup_table = data["specification"]["preposition_lookup"]

        self.synthesis.max_degree = data.get("synthesis_config", {}).get("maximal_polynomial_degree", self.synthesis.max_degree)
        self.synthesis.epsilon = data.get("synthesis_config", {}).get("epsilon", self.synthesis.epsilon)
        self.synthesis.probability = data.get("synthesis_config", {}).get("probability_threshold", self.synthesis.probability)
        self.synthesis.theorem = data.get("synthesis_config", {}).get("theorem_name", self.synthesis.theorem)
        self.synthesis.solver = data.get("synthesis_config", {}).get("solver_name", self.synthesis.solver)
        self.synthesis.owl_path = data.get("synthesis_config", {}).get("owl_path", self.synthesis.owl_path)


    def _high_level_description(self):
        st.subheader("System Description")
        col1, col2, col3 = st.columns(3, gap="medium")
        self.high_level_description.state_dim = col1.selectbox(
            label="State dimension",
            options=list(range(1, 5)),
            index=self.high_level_description.state_dim - 1
        )
        self.high_level_description.control_dim = col2.selectbox(
            label="Control policy dimension",
            options=list(range(0, 4)),
            index=self.high_level_description.control_dim,
            help="Set this to zero if it is a system verification task"
        )
        self.high_level_description.disturbance_dim = col3.selectbox(
            label="Disturbance dimension",
            options=[0, 1],
            index=self.high_level_description.disturbance_dim
        )
        rcol1, rcol2 = st.columns(2, gap="medium")
        self.high_level_description.system_space = rcol1.text_input(
            label="System space",
            value=self.high_level_description.system_space,
            help="You can only use {'<', '<=', '>', '>='} operators"
        )
        self.high_level_description.initial_space = rcol2.text_input(
            label="Initial space",
            value=self.high_level_description.initial_space,
            help="You can only use {'<', '<=', '>', '>='} operators"
        )

        if self.high_level_description.control_dim == 0:
            self.high_level_description.config_type = ConfigType.SYSTEM_VERIFICATION

    def _actions(self):
        st.subheader("Control Actions")
        if self.high_level_description.control_dim == 0:
            st.write('<span style="color: gray;">No control policy in system verification mode!</span>', unsafe_allow_html=True)
            return
        st.write('<span style="color: gray;">Available state variables: ' + ", ".join(f"S{i+1}" for i in range(self.high_level_description.state_dim))+"</span>", unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="medium")
        self.actions.max_degree = col1.selectbox(
            label="Max degree",
            options=list(range(0, 6)),
            index=self.actions.max_degree
        )
        extended_policy = (self.actions.control_policy + [""] * self.actions.max_degree)[:self.actions.max_degree]
        self.actions.control_policy = [
            col2.text_input(
                label=f"π {i+1}",
                value=extended_policy[i]
            )
            for i in range(self.actions.max_degree)
        ]

        if any(bool(action) for action in self.actions.control_policy):
            self.high_level_description.config_type = ConfigType.POLICY_VERIFICATION
        elif self.high_level_description.control_dim == 0:
            self.high_level_description.config_type = ConfigType.SYSTEM_VERIFICATION
        else:
            self.high_level_description.config_type = ConfigType.POLICY_SYNTHESIS

    def _disturbance(self):
        st.subheader("Disturbance")
        col1, col2 = st.columns(2, gap="medium")
        self.disturbance.name = col1.selectbox(
            label="Distribution",
            options=self.disturbance.get_valid_distributions(),
            index=self.disturbance.get_valid_distributions().index(self.disturbance.name)
        )
        special_parameters = self.disturbance.get_special_parameters()
        if special_parameters:
            self.disturbance.parameters = {
                key: [col2.number_input(
                    label=key,
                    value=self.disturbance.parameters.get(key, [0.0])[0]
                )]
                for key in special_parameters
            }

    def _dynamics(self):
        st.subheader("Dynamics")
        available_variables = f"Available state variables: {'{'+", ".join(f"S{i+1}" for i in range(self.high_level_description.state_dim))+'}'} " + \
                            f"Available control variables: {'{'+", ".join(f"A{i+1}" for i in range(self.high_level_description.control_dim))+'}'} " + \
                            f"Available disturbance variables: {'{'+", ".join(f"D{i+1}" for i in range(self.high_level_description.disturbance_dim))+'}'}"
        no_action = self.high_level_description.control_dim == 0
        no_disturbance = self.high_level_description.disturbance_dim == 0
        for idx in range(len(self.system_definition.dynamics)):
            with st.expander(f"Dynamic {idx + 1}", expanded=True):
                rcol1, rcol2 = st.columns(2, gap="medium")
                self.system_definition.dynamics[idx]["condition"] = rcol1.text_input(
                    label="Condition",
                    value=self.system_definition.dynamics[idx].get("condition", "0 <= 1"),
                    key=f"condition_{idx}",
                    help="If you dont need piecewise dynamics, you can use '0 <= 1' as your condition. Available operators: {<, <=, >, >=}"
                )
                transformations = (self.system_definition.dynamics[idx].get("transforms", []) +
                                   [""] * self.high_level_description.state_dim
                                   )[:self.high_level_description.state_dim]
                self.system_definition.dynamics[idx]["transforms"] = [
                    transformation_helper(
                        label=f"S{i + 1}'",
                        default=transformations[i],
                        no_action=no_action,
                        no_disturbance=no_disturbance,
                        placeholder=rcol2,
                        key=f"transform_{idx}_{i}",
                        help=available_variables
                    )
                    for i in range(self.high_level_description.state_dim)
                ]

        def add_transformation():
            self.system_definition.dynamics.append({
                "condition": "0 <= 1",
                "transforms": [""] * self.high_level_description.state_dim
            })
            st.session_state["add_new_transformation"] = False

        if "add_new_transformation" not in st.session_state:
            st.session_state["add_new_transformation"] = False

        st.checkbox(
            "Add new transformation",
            value=st.session_state["add_new_transformation"],
            key="add_new_transformation",
            on_change=add_transformation
        )

    def _specification(self):
        st.subheader("Specification")
        self.specification.formula = st.text_input(
            label="LTL formula",
            value=self.specification.formula
        ).replace("true", "TRUE").replace("false", "FALSE")
        col1, col2 = st.columns(2, gap="medium")
        detected_atomic_prepositions = set(self.specification.formula) & possible_atomic_propositions
        self.specification.formula = self.specification.formula.replace("TRUE", "true").replace("FALSE", "false")
        self.specification.need_lookup_table = col1.checkbox(
            label="Lookup table",
            value=self.specification.need_lookup_table
        )
        if len(detected_atomic_prepositions) > 0:
            self.specification.need_lookup_table = True
        if self.specification.need_lookup_table:
            col1.write('<span style="color: #b8b56e;">Atomic preposition should be form of a-z</span>', unsafe_allow_html=True)
        if self.specification.need_lookup_table and len(detected_atomic_prepositions) > 0:
            self.specification.lookup_list = list(detected_atomic_prepositions)
            self.specification.lookup_list.sort()
            col1.write(f'<span style="color: gray;">Detected atomic propositions: {", ".join(self.specification.lookup_list)}</span>', unsafe_allow_html=True)
            self.specification.lookup_table = {
                atomic: col2.text_input(
                    label=f"Atomic proposition '{atomic}'",
                    value=self.specification.lookup_table.get(atomic, "")
                )
                for atomic in self.specification.lookup_list
            }

    def _synthesis(self):
        st.subheader("Synthesis")
        col1, col2 = st.columns(2, gap="medium")
        self.synthesis.max_degree = col1.selectbox(
            label="Max degree",
            options=list(range(1, 6)),
            index=self.synthesis.max_degree - 1
        )
        self.synthesis.epsilon = col1.number_input(
            label="Epsilon (x1e-15)",
            step=1.0,
            value=self.synthesis.epsilon * 1e15
        ) * 1e-15
        self.synthesis.probability = col1.number_input(
            label="Probability threshold (x100)",
            step=1.0,
            min_value=0.0,
            max_value=100.0,
            value=self.synthesis.probability * 100
        ) / 100
        self.synthesis.theorem = col2.selectbox(
            label="Theorem",
            options=possible_theorems,
            index=possible_theorems.index(self.synthesis.theorem)
        )
        self.synthesis.solver = col2.selectbox(
            label="Solver",
            options=Possible_solvers,
            index=Possible_solvers.index(self.synthesis.solver)
        )
        self.synthesis.owl_path = col2.text_input(
            label="Path to OWL executable",
            value=self.synthesis.owl_path
        )
        if not os.path.exists(self.synthesis.owl_path):
            col2.write('<span style="color: #b16a6a;">Executable not found</span>', unsafe_allow_html=True)
        else: # write with some suitable green
            col2.write('<span style="color: #6ab16a;">Executable found</span>', unsafe_allow_html=True)

    def view(self):
        st.title("Configuration")
        status = st.empty()
        st.divider()
        self._high_level_description()
        st.divider()
        self._actions()
        st.divider()
        self._disturbance()
        st.divider()
        self._dynamics()
        st.divider()
        self._specification()
        st.divider()
        self._synthesis()
        st.divider()
        status.write(f'<span style="color: gray;">System status: {self.high_level_description.config_type.value}</span>',unsafe_allow_html=True)

    def get_tool_input(self):
        actions = {
            "action_dimension": self.high_level_description.control_dim,
            "state_dimension": self.high_level_description.state_dim,
            "maximal_degree": self.actions.max_degree,
            "policies": self.actions.control_policy,
        }
        disturbance = {
            "dimension": self.high_level_description.disturbance_dim,
            "distribution_name": self.disturbance.name,
            "distribution_generator_parameters": self.disturbance.parameters,
        }
        synthesis_config = {
            "maximal_polynomial_degree": self.synthesis.max_degree,
            "probability_threshold": self.synthesis.probability,
            "epsilon": self.synthesis.epsilon,
            "theorem_name": self.synthesis.theorem,
            "solver_name": self.synthesis.solver,
            "owl_path": self.synthesis.owl_path,
        }
        specification = {
            "ltl_formula": self.specification.formula,
            "predicate_lookup": self.specification.lookup_table,
            "owl_binary_path": self.synthesis.owl_path,
            "hoa_path": None,
        }
        _system_dynamic_equations = [
            ConditionalDynamics(
                condition=extract_space_inequalities(item["condition"]),
                dynamics=[Equation.extract_equation_from_string(eq) for eq in item["transforms"]]
            )
            for item in self.system_definition.dynamics
        ]
        system_dynamic = {
            "state_dimension": self.high_level_description.state_dim,
            "action_dimension": self.high_level_description.control_dim,
            "disturbance_dimension": self.high_level_description.disturbance_dim,
            "system_transformations": _system_dynamic_equations
        }
        return ToolInput(
            actions_pre=actions,
            disturbance_pre=disturbance,
            sds_pre=system_dynamic,
            synthesis_config_pre=synthesis_config,
            specification_pre=specification,
            system_space_pre=self.high_level_description.system_space,
            initial_space_pre=self.high_level_description.initial_space
        )



