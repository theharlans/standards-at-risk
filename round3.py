from app.agents.registry import get_agent_prompts
from app.llm import get_llm_client
from app.state import SwarmState, AgentRoundOutput

ATTACK_MAP = {
    "InterDigital Strategist": "Amazon Strategist",
    "Amazon Strategist": "InterDigital Strategist",
    "UK Judge": "Both parties",
    "UPC Judge": "Enforcement assumptions",
    "US/ITC Agent": "US leverage relevance",
    "Strategic Shift Analyst": "System dynamics",
    "Adversarial Critic": "All agents",
    "PTAB/Validity Agent": "Portfolio strength assumptions",
    "Regulatory/Competition Agent": "Enforcement legitimacy assumptions",
    "Standards Essentiality Agent": "FRAND scope assumptions",
}


def _build_context(state: SwarmState) -> str:
    parts = ["Round 1 + Round 2 context:", ""]
    for item in state.round_1_outputs:
        parts.append(f"{item.agent_name} (R1)")
        if item.position:
            parts.append(f"Position: {item.position}")
        parts.append("")
    for item in state.round_2_outputs:
        parts.append(f"{item.agent_name} (R2)")
        if item.pressure_assessment:
            parts.append(f"Pressure: {item.pressure_assessment}")
        if item.amazon_strategy_assessment:
            parts.append(f"Amazon Strategy: {item.amazon_strategy_assessment}")
        parts.append("")
    return "\n".join(parts).strip()


def run_round_3(state: SwarmState) -> SwarmState:
    llm = get_llm_client()
    agent_prompts = get_agent_prompts()
    context = _build_context(state)
    outputs = []

    for agent_name in state.agent_names:
        print(f"\n=== Running agent: {agent_name} (Round 3) ===")

        agent_prompt = agent_prompts[agent_name]
        target = ATTACK_MAP[agent_name]

        system_prompt = "\n\n".join([
            state.system_prompt,
            agent_prompt,
        ])

        user_prompt = f"""
Context:
{context}

Task:
Round 3: Conflict and Critique

You must challenge weaknesses in the system.

Your target:
{target}

Instructions:
1. Identify a flawed assumption or weak reasoning.
2. Explain why it is flawed.
3. Provide a corrected or alternative view.
4. Identify one second-order consequence of being wrong.

Required output format (strict):

Target:
<who or what you are attacking>

Flaw:
<one clear flaw>

Why it is flawed:
<2-4 sentences>

Correction:
<what a better view looks like>

Second-Order Risk:
<what happens if the flawed view is followed>

Rules:
- Be direct, not polite
- Do not repeat earlier reasoning
- Focus on breaking assumptions
""".strip()

        text = llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)

        output = AgentRoundOutput(
            agent_name=agent_name,
            round_name="round_3",
            raw_text=text,
        )
        outputs.append(output)

    state.round_3_outputs = outputs
    return state
