from typing import List, Optional, Literal
from pydantic import BaseModel, Field


AgentName = Literal[
    "InterDigital Strategist",
    "Amazon Strategist",
    "UK Judge",
    "UPC Judge",
    "US/ITC Agent",
    "Strategic Shift Analyst",
    "Adversarial Critic",
    "PTAB/Validity Agent",
    "Regulatory/Competition Agent",
    "Standards Essentiality Agent",
]


class AgentRoundOutput(BaseModel):
    agent_name: AgentName
    round_name: str
    raw_text: str

    position: Optional[str] = None
    why: Optional[str] = None
    second_order_effect: Optional[str] = None

    pressure_assessment: Optional[str] = None
    amazon_strategy_assessment: Optional[str] = None


class SwarmState(BaseModel):
    run_id: str
    article_path: str
    article_title: str
    article_text: str

    system_prompt: str
    decision_tree: str

    agent_names: List[AgentName]

    model_provider: str
    model_name: str

    output_dir: str

    fact_ledger: Optional[str] = None
    latent_factors: Optional[str] = None

    round_1_outputs: List[AgentRoundOutput] = Field(default_factory=list)
    round_2_outputs: List[AgentRoundOutput] = Field(default_factory=list)
    round_3_outputs: List[AgentRoundOutput] = Field(default_factory=list)
    round_4_outputs: List[AgentRoundOutput] = Field(default_factory=list)
    round_5_outputs: List[AgentRoundOutput] = Field(default_factory=list)
    round_6_output: Optional[AgentRoundOutput] = None
    coverage_audit_output: Optional[AgentRoundOutput] = None
    final_refinement_output: Optional[AgentRoundOutput] = None
