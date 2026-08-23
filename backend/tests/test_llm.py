import pytest
from backend.app.services.llm_service import llm_service
from backend.app.schemas import SummaryStructured

SAMPLE_TRANSCRIPT = """
Alice: Let's finalize the database choice today. Bob, what do you think?
Bob: I recommend PostgreSQL with pgvector. It saves 40% in cost.
Carol: Agreed. Let's decide on PostgreSQL.
Alice: Decision made: We approve PostgreSQL.
Alice: Action items: Bob will write migration scripts by Friday. Carol will update Figma designs by Wednesday.
"""

@pytest.mark.asyncio
async def test_llm_summary_generation():
    summary_data, provider = await llm_service.summarize(SAMPLE_TRANSCRIPT, provider="fallback")
    
    assert isinstance(summary_data, SummaryStructured)
    assert len(summary_data.title) > 0
    assert len(summary_data.executive_summary) > 10
    assert len(summary_data.key_decisions) > 0
    assert len(summary_data.action_items) > 0
    
    # Verify action items structure
    first_item = summary_data.action_items[0]
    assert first_item.task is not None
    assert first_item.assignee is not None
    assert first_item.priority in ["High", "Medium", "Low"]

@pytest.mark.asyncio
async def test_empty_transcript_handling():
    with pytest.raises(ValueError):
        await llm_service.summarize("")
