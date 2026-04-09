from pathlib import Path
from app.config import get_settings
from app.graph import build_graph
from app.state import SwarmState
from app.utils.ids import make_run_id
from app.utils.io import read_text_file


def main():
    settings = get_settings()

    article_path = "inputs/part3_enriched_input.txt"

    article_text = read_text_file(article_path)
    system_prompt = read_text_file("app/prompts/system.md")
    decision_tree = read_text_file("app/prompts/decision_tree.md")

    run_id = make_run_id()
    output_dir = f"outputs/{run_id}"

    state = SwarmState(
        run_id=run_id,
        article_path=article_path,
        article_title=Path(article_path).stem,
        article_text=article_text,
        system_prompt=system_prompt,
        decision_tree=decision_tree,
        agent_names=[
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
        ],
        model_provider=settings.MODEL_PROVIDER,
        model_name=settings.MODEL_NAME,
        output_dir=output_dir,
    )

    graph = build_graph()
    graph.invoke(state)


if __name__ == "__main__":
    main()
