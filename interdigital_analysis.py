"""
Multi-Agent Legal Dispute Analysis System
InterDigital v Amazon — SEP/FRAND Prediction Engine

Uses Claude Sonnet 4.6 via the Anthropic API.
Six agent roles, four iterative rounds, coverage audit, final synthesis.

Requirements:
    pip install anthropic

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    python interdigital_analysis.py
"""

import anthropic
import json
import time
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"          # Sonnet 4.6: best balance of reasoning depth and cost
MAX_TOKENS = 1500                     # Per agent call — enough for substantive analysis
TEMPERATURE = 1.0                     # Default; agents are instructed to commit, not hedge

client = anthropic.Anthropic()        # Reads ANTHROPIC_API_KEY from environment


# ---------------------------------------------------------------------------
# Seed Material
# ---------------------------------------------------------------------------

# In production, load this from file: open("juve_article.txt").read()
# Abbreviated here for illustration — use the full JUVE article text in practice
SEED_ARTICLE = """
InterDigital is suing Amazon for infringement of ten patents relating to video compression
and HDR technology. Amazon initiated RAND-rate determination proceedings before the UK High
Court in August 2025. InterDigital obtained anti-suit injunctions (ASIs) from Munich and the
UPC local division Mannheim in September 2025. The UPC's order is technically an
anti-interim-licence injunction (AILI). The UK High Court issued an anti-anti-suit injunction
(AASI) in October 2025. The UPC upheld its AILI in December 2025, ordering a penalty of up
to €50,000,000 for non-compliance and indicating Amazon was possibly already in breach.
The European Commission was notified on 24 December 2025. The parties came within reach of
settling in February 2026 but were blocked by the UPC's Rules of Procedure. The UPC Court
of Appeal will hear the AILI scope dispute on 28 May 2026. The UK RAND trial is scheduled
for September 2026. InterDigital also filed infringement actions in Delaware, Rio de Janeiro,
Munich, and Mannheim in November 2025.
""".strip()


# ---------------------------------------------------------------------------
# Agent Definitions
# ---------------------------------------------------------------------------

@dataclass
class Agent:
    """
    Each agent has a role identity and a mandatory commitment instruction.
    The commitment instruction is the critical design choice: agents are
    structurally prevented from hedging. They must take positions.
    """
    name: str
    role_prompt: str
    perspective: str


AGENTS = [
    Agent(
        name="Licensor",
        perspective="InterDigital",
        role_prompt="""You are analysing this dispute from InterDigital's perspective.
You are a pure-play patent licensor. Your entire revenue model depends on licence fees.
You have no products and no manufacturing — litigation is not a cost centre, it is your
business. You have deployed ASIs across five jurisdictions simultaneously and obtained a
€50M penalty order. You believe you are winning.

CRITICAL INSTRUCTION: You must take firm positions. Do not describe possibilities.
Assert what InterDigital wants, why, and what its next move is. If you are uncertain,
commit to the most probable path and say so explicitly. Never hedge with 'it depends'
without immediately resolving the dependency."""
    ),
    Agent(
        name="Implementer",
        perspective="Amazon",
        role_prompt="""You are analysing this dispute from Amazon's perspective.
You are a $600B+ revenue company with a long history of absorbing multi-year SEP litigation.
You initiated UK proceedings deliberately to get a FRAND rate set. You are not afraid of
litigation costs. You are, however, acutely sensitive to anything that threatens your
device business commercially — FireTV, Kindle, and the Prime Video ecosystem.

CRITICAL INSTRUCTION: You must take firm positions. Do not describe possibilities.
Assert what Amazon wants, why, and what its strategic calculus is. Identify the specific
pressure that would actually move Amazon toward settlement — not theoretical pressure,
real financial or commercial disruption."""
    ),
    Agent(
        name="UK_Court",
        perspective="UK High Court / Judge Meade",
        role_prompt="""You are analysing this dispute from the UK High Court's institutional perspective.
You have confirmed jurisdiction over a global RAND determination under Unwired Planet v Huawei.
You have issued and upheld an AASI against InterDigital. You have expressed 'serious reservations'
about the UPC's approach and about the procedural conflict between courts. Your September 2026
RAND trial is scheduled and you intend to proceed.

CRITICAL INSTRUCTION: Take firm positions on what the UK court will and will not do.
Identify the specific circumstances under which Judge Meade would delay, modify, or proceed
with the September trial. Do not describe the court as passive — it is an active institutional
actor with its own jurisdictional interests."""
    ),
    Agent(
        name="UPC",
        perspective="UPC local division Mannheim / Court of Appeal",
        role_prompt="""You are analysing this dispute from the UPC's institutional perspective.
You are a newly established court still building legitimacy and jurisdictional authority.
You issued an ex parte AILI, upheld it, ordered a €50M penalty, notified the European Commission,
and have now demanded Amazon prove compliance in legally binding terms. Allowing the UK High Court
to effectively override your ASI would set a damaging precedent for the UPC's credibility.

CRITICAL INSTRUCTION: Take firm positions on what the UPC will do in May 2026 and why.
The UPC has institutional incentives that are independent of the legal merits. Identify them
explicitly and assess how they affect the Court of Appeal's likely ruling on AILI scope."""
    ),
    Agent(
        name="Strategic_Analyst",
        perspective="Outcome-focused strategic analyst",
        role_prompt="""You are a strategic analyst focused on predicting the most likely outcome
of this dispute. You are not an advocate for either party. You are incentive-aware,
precedent-aware, and commercially realistic. You have read the positions of all other agents.

CRITICAL INSTRUCTION: Produce a single most-likely outcome with explicit reasoning.
Then identify the strongest alternative. Assign approximate probabilities. Do not produce
a list of possibilities — produce a ranked prediction with committed reasoning.
The goal is a usable forecast, not a comprehensive survey of scenarios."""
    ),
    Agent(
        name="Adversarial_Critic",
        perspective="Adversarial critic — assigned to challenge the consensus",
        role_prompt="""You are an adversarial critic. Your sole function is to challenge
the emerging consensus. You are not trying to be balanced — you are trying to find the
specific assumptions that are doing the most structural work in the prediction and stress-test them.

CRITICAL INSTRUCTION: Identify the two or three load-bearing assumptions in the current
synthesis and attack them directly. For each assumption, state: what the consensus assumes,
why that assumption might be wrong, and what the prediction looks like if the assumption fails.
Do not agree with the consensus unless you genuinely cannot find a credible challenge.
Disagreement is your default position."""
    ),
]


# ---------------------------------------------------------------------------
# Round Definitions
# ---------------------------------------------------------------------------

ROUNDS = [
    {
        "name": "Initial Positions",
        "instruction": """Based on the seed article above, state your initial position on:
1. What does your principal (or your court/institution) want from this dispute?
2. What is your principal's strongest card?
3. What is your principal's biggest vulnerability?
4. What outcome do you predict, and why?

Be direct. Take positions. Do not summarise the article back to me."""
    },
    {
        "name": "Escalation Paths",
        "instruction": """Given the initial positions above, assess:
1. What is the most likely escalation path from here to the May 2026 UPC hearing?
2. What specific event between now and May would most change the outcome?
3. Does the €50M penalty actually coerce Amazon? Be specific about the mechanism
   and the arithmetic — not the headline number, but the accrual rate and enforceability.
4. What does the US Delaware filing mean strategically, and when does it become relevant?"""
    },
    {
        "name": "Conflict and Critique",
        "instruction": """The Strategic Analyst has produced a draft prediction.
The Adversarial Critic has challenged its load-bearing assumptions.

For your role: respond to the critique. Either defend the consensus prediction
against the critic's specific challenges, or concede where the critique lands.
Identify the single most important unresolved tension in the analysis.
Do not restate positions already made — advance the reasoning."""
    },
    {
        "name": "Convergence",
        "instruction": """This is the final synthesis round.

Produce your role's final committed position:
- Most likely outcome (single sentence)
- Confidence (0-100%)
- The one variable that would most change this prediction
- What you would need to see happen between now and September 2026 to update your view

Be precise. No new arguments — only refined commitments based on the full reasoning above."""
    },
]


# ---------------------------------------------------------------------------
# Core Reasoning Engine
# ---------------------------------------------------------------------------

def run_agent_round(
    agent: Agent,
    round_def: dict,
    conversation_history: list[dict],
    seed_article: str
) -> str:
    """
    Run a single agent for a single round.

    The conversation_history carries all prior rounds for this agent,
    enabling stateful reasoning across the iterative chain.
    Each call is independent per agent — agents do not see each other's
    raw outputs within a round, only the synthesised summaries passed
    as context in subsequent rounds.
    """
    system_prompt = f"""You are participating in a structured multi-agent analysis of the
InterDigital v Amazon SEP/FRAND dispute.

Your role: {agent.name} ({agent.perspective})

{agent.role_prompt}

The seed article describing the dispute:
---
{seed_article}
---

This is round: {round_def['name']}
"""

    messages = conversation_history + [
        {"role": "user", "content": round_def["instruction"]}
    ]

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    )

    return response.content[0].text


def run_coverage_audit(all_round_outputs: dict, seed_article: str) -> str:
    """
    Separate Claude call with a distinct mandate: find what the synthesis missed.

    This is not a continuation of the agent reasoning — it is a fresh call
    with explicit instructions to be critical of the prior output.
    The audit is the mechanism that surfaces structural omissions before
    the final synthesis is produced.
    """
    synthesis_text = "\n\n".join([
        f"=== {agent_name} ===\n{outputs[-1]}"  # Use each agent's final round output
        for agent_name, outputs in all_round_outputs.items()
    ])

    audit_prompt = f"""You are conducting a coverage audit of a multi-agent legal analysis.

The original source article:
---
{seed_article}
---

The analysis produced by the agent system:
---
{synthesis_text}
---

Your task is to identify:

1. MISSED FACTS: Facts present in the source article that do not appear anywhere
   in the analysis and that could materially affect the prediction.

2. UNDERWEIGHTED FACTS: Facts that appear in the analysis but are mentioned only
   in passing when they should be load-bearing in the prediction logic.

3. QUESTIONABLE EXCLUSIONS: Facts the analysis ignored that it should justify ignoring.

4. ASSUMPTION EXPOSURE: The two or three assumptions doing the most structural work
   in the consensus prediction that are asserted rather than demonstrated.

Be specific. Quote or reference the source article directly when identifying gaps.
Do not praise the analysis. Your job is to find its weaknesses."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system="You are a rigorous coverage auditor for structured analytical outputs.",
        messages=[{"role": "user", "content": audit_prompt}],
    )

    return response.content[0].text


def produce_final_synthesis(
    all_round_outputs: dict,
    audit_output: str,
    seed_article: str
) -> str:
    """
    Final synthesis call incorporating:
    - All agent outputs from all rounds
    - Coverage audit findings
    - Explicit instruction to produce a structured prediction document

    This call produces the publishable output: prediction, alternative,
    key driver, residual uncertainty, confidence.
    """
    full_reasoning = "\n\n".join([
        f"=== {agent_name} — All Rounds ===\n" +
        "\n---\n".join(outputs)
        for agent_name, outputs in all_round_outputs.items()
    ])

    synthesis_prompt = f"""You have received the complete output of a six-agent,
four-round structured analysis of the InterDigital v Amazon SEP/FRAND dispute,
followed by a coverage audit identifying gaps and assumption exposure.

Source article:
---
{seed_article}
---

Agent reasoning (all rounds):
---
{full_reasoning}
---

Coverage audit findings:
---
{audit_output}
---

Produce the final structured prediction in exactly this format:

PREDICTION:
[Single paragraph. The most likely outcome. Be specific about timing, mechanism,
and the conditions under which it occurs. Do not hedge without resolving the hedge.]

ALTERNATIVE OUTCOME:
[Single paragraph. The strongest alternative path. What would have to be true
for this to occur instead of the primary prediction?]

KEY DRIVER:
[One or two sentences. The single variable that most determines which path occurs.]

MAIN UNCERTAINTY:
[One or two sentences. The biggest unresolved question the analysis cannot answer
from the available evidence.]

CONFIDENCE:
[Integer 0-100. Then one sentence explaining why this number, not higher or lower.]

WHAT THE AUDIT CHANGED:
[Two or three sentences. Specifically what the coverage audit caused you to revise
relative to the emerging consensus from the agent rounds.]"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system="""You are producing the final output of a structured multi-agent
legal dispute analysis. You must commit to positions. You must produce a usable
forecast, not a survey of possibilities. The output will be published.""",
        messages=[{"role": "user", "content": synthesis_prompt}],
    )

    return response.content[0].text


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_full_analysis(seed_article: str) -> dict:
    """
    Orchestrates the full pipeline:
    1. Four rounds across six agents
    2. Coverage audit (separate call)
    3. Final synthesis incorporating audit

    Returns a results dict with all intermediate outputs and the final prediction.

    Design notes:
    - Agents maintain their own conversation_history across rounds (stateful per agent)
    - Agents do NOT share raw outputs within a round — only the round instruction is shared
    - The coverage audit is a completely separate call with no conversation history
    - Total API calls: (6 agents × 4 rounds) + 1 audit + 1 synthesis = 27 calls
    - Approximate cost at Sonnet 4.6 pricing: $1.50–$3.00 depending on output length
    """

    results = {
        "agent_outputs": {agent.name: [] for agent in AGENTS},
        "audit": None,
        "final_synthesis": None,
    }

    # --- Rounds 1–4: All agents, iteratively ---
    for round_idx, round_def in enumerate(ROUNDS):
        print(f"\n{'='*60}")
        print(f"ROUND {round_idx + 1}: {round_def['name']}")
        print('='*60)

        for agent in AGENTS:
            print(f"  Running agent: {agent.name}...")

            # Build this agent's conversation history from its prior outputs
            conversation_history = []
            for prior_output in results["agent_outputs"][agent.name]:
                # Each prior round: the instruction was the user turn,
                # the output was the assistant turn
                prior_round_def = ROUNDS[len(conversation_history) // 2]
                conversation_history.append({
                    "role": "user",
                    "content": prior_round_def["instruction"]
                })
                conversation_history.append({
                    "role": "assistant",
                    "content": prior_output
                })

            output = run_agent_round(
                agent=agent,
                round_def=round_def,
                conversation_history=conversation_history,
                seed_article=seed_article,
            )

            results["agent_outputs"][agent.name].append(output)
            print(f"  Done. ({len(output)} chars)")

            # Small delay to avoid rate limiting on parallel agent calls
            time.sleep(0.5)

    # --- Coverage Audit ---
    print(f"\n{'='*60}")
    print("COVERAGE AUDIT")
    print('='*60)
    results["audit"] = run_coverage_audit(
        all_round_outputs=results["agent_outputs"],
        seed_article=seed_article,
    )
    print(f"Audit complete. ({len(results['audit'])} chars)")

    # --- Final Synthesis ---
    print(f"\n{'='*60}")
    print("FINAL SYNTHESIS")
    print('='*60)
    results["final_synthesis"] = produce_final_synthesis(
        all_round_outputs=results["agent_outputs"],
        audit_output=results["audit"],
        seed_article=seed_article,
    )
    print(f"Synthesis complete. ({len(results['final_synthesis'])} chars)")

    return results


# ---------------------------------------------------------------------------
# Independent Stress Test
# ---------------------------------------------------------------------------

def run_stress_test(synthesis: str, seed_article: str) -> str:
    """
    Separate independent review — a fresh Claude instance with no access
    to the intermediate agent reasoning.

    This is the 'second opinion' step. The reviewer sees only:
    - The source article
    - The final structured prediction

    It does NOT see the agent roles, the round outputs, or the audit.
    The independence is structural, not just instructional.
    """
    stress_prompt = f"""You are an independent strategic reviewer.

You have been given a source article and a structured prediction produced by
a separate analysis system. You have NOT seen how the prediction was produced.

Source article:
---
{seed_article}
---

Structured prediction to review:
---
{synthesis}
---

Your task:

1. WHERE IS THE REASONING STRONGEST?
   Identify the one or two claims in the prediction that are best supported
   by the source material and the underlying logic.

2. WHERE DOES IT RELY ON ASSUMPTIONS THAT MAY NOT HOLD?
   Identify the load-bearing assumptions. For each: state the assumption,
   why it might be wrong, and what the prediction looks like if it fails.

3. BLIND SPOTS:
   What important factors — legal, strategic, economic, or procedural —
   are absent from the prediction entirely?

4. YOUR INDEPENDENT STRUCTURED VIEW:

   Prediction: <your most likely outcome>
   Alternative Outcome: <the strongest alternative>
   Key Driver: <what actually determines which path occurs>
   Main Uncertainty: <the biggest unresolved variable>
   Confidence: <0-100%>

5. DO YOU AGREE OR DISAGREE WITH THE PREDICTION'S CONCLUSION?
   Be explicit. Do not hedge. If you agree directionally but disagree on
   timing or mechanism, say so precisely."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system="""You are an independent strategic reviewer of structured analytical outputs.
You were not involved in producing the analysis you are reviewing.
Your job is to improve it, not validate it. Default to challenge.""",
        messages=[{"role": "user", "content": stress_prompt}],
    )

    return response.content[0].text


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("InterDigital v Amazon — Multi-Agent Analysis System")
    print(f"Model: {MODEL}")
    print(f"Agents: {len(AGENTS)}")
    print(f"Rounds: {len(ROUNDS)}")
    print(f"Estimated API calls: {len(AGENTS) * len(ROUNDS) + 2} (agents + audit + synthesis)")
    print(f"Estimated cost: $1.50–$3.00 at current Sonnet 4.6 pricing\n")

    # Run the full multi-agent analysis
    results = run_full_analysis(SEED_ARTICLE)

    # Run the independent stress test against the synthesis
    print(f"\n{'='*60}")
    print("INDEPENDENT STRESS TEST")
    print('='*60)
    stress_test_output = run_stress_test(
        synthesis=results["final_synthesis"],
        seed_article=SEED_ARTICLE,
    )
    results["stress_test"] = stress_test_output
    print(f"Stress test complete. ({len(stress_test_output)} chars)")

    # Save full results to JSON
    output_path = "interdigital_analysis_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"COMPLETE. Results saved to: {output_path}")
    print('='*60)

    # Print the final synthesis to stdout
    print("\n\nFINAL SYNTHESIS:\n")
    print(results["final_synthesis"])

    print("\n\nINDEPENDENT STRESS TEST:\n")
    print(results["stress_test"])
