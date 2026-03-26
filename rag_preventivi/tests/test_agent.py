# tests/test_agent.py
from unittest.mock import patch, MagicMock
from agno.db.in_memory import InMemoryDb


def test_build_chat_agent_has_history_and_db():
    """build_chat_agent deve configurare multi-turno con InMemoryDb."""
    mock_knowledge = MagicMock()
    mock_vector_db = MagicMock()
    with patch("agent.build_knowledge", return_value=(mock_knowledge, mock_vector_db)):
        from agent import build_chat_agent
        agent_instance = build_chat_agent()
    assert agent_instance.add_history_to_context is True
    assert isinstance(agent_instance.db, InMemoryDb)
