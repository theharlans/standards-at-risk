from app.agents import (
    interdigital,
    amazon,
    uk_judge,
    upc_judge,
    us_itc,
    strategic_shift,
    critic,
    ptab_validity,
    regulatory_competition,
    standards_essentiality,
)


def get_agent_prompts():
    return {
        "InterDigital Strategist": interdigital.get_prompt(),
        "Amazon Strategist": amazon.get_prompt(),
        "UK Judge": uk_judge.get_prompt(),
        "UPC Judge": upc_judge.get_prompt(),
        "US/ITC Agent": us_itc.get_prompt(),
        "Strategic Shift Analyst": strategic_shift.get_prompt(),
        "Adversarial Critic": critic.get_prompt(),
        "PTAB/Validity Agent": ptab_validity.get_prompt(),
        "Regulatory/Competition Agent": regulatory_competition.get_prompt(),
        "Standards Essentiality Agent": standards_essentiality.get_prompt(),
    }
