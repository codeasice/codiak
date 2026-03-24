"""Categorization pipeline orchestrator."""
import logging
from api.services.dragon_keeper.rules_engine import run_rules_engine
from api.services.dragon_keeper.llm_categorizer import run_llm_categorizer

logger = logging.getLogger("dragon_keeper.categorization")


def run_categorization_pipeline(
    reprocess: bool = False,
    llm_limit: int | None = None,
) -> dict:
    """Run the full categorization pipeline: rules -> LLM -> manual queue.

    Args:
        reprocess: If True, re-run rules on pending_review items and allow
                   LLM to re-suggest for items without a suggestion yet.
        llm_limit: Max transactions for LLM to process this run. None uses the default.
    """
    results = {}

    rules_result = run_rules_engine(reprocess=reprocess)
    results["rules_engine"] = rules_result
    logger.info("Pipeline tier 1 (rules): %s", rules_result)

    llm_result = run_llm_categorizer(max_transactions=llm_limit)
    results["llm_categorizer"] = llm_result
    logger.info("Pipeline tier 2 (LLM): %s", llm_result)

    return results
