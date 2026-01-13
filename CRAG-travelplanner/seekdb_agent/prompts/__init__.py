"""
CRAG TravelPlanner Prompts
===========================
定义用于各个LLM调用节点的Prompt模板
"""

from seekdb_agent.prompts.ask_user import ASK_USER_PROMPT
from seekdb_agent.prompts.collector import COLLECTOR_PROMPT
from seekdb_agent.prompts.evaluator import EVALUATOR_PROMPT
from seekdb_agent.prompts.generator import GENERATOR_PROMPT
from seekdb_agent.prompts.refiner import REFINER_PROMPT

__all__ = [
    "COLLECTOR_PROMPT",
    "EVALUATOR_PROMPT",
    "REFINER_PROMPT",
    "GENERATOR_PROMPT",
    "ASK_USER_PROMPT",
]
