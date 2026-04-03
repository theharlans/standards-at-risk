# Standards at Risk

Multi-agent AI analysis of SEP/FRAND patent disputes.
Companion code for the [Standards at Risk Substack](your-substack-url).

## InterDigital v Amazon

`interdigital_analysis.py` implements the six-agent, four-round reasoning
system described in the article. It uses Claude Sonnet 4.6 via the Anthropic API.

## Setup

pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
python interdigital_analysis.py

## Note

The seed article in the file is abbreviated. Replace the `SEED_ARTICLE`
variable with the full JUVE Patent article text for a complete run, located here https://www.juve-patent.com/cases/interdigital-vs-amazon-a-chronology-of-the-escalation/
