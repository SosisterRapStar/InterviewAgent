import json
import os
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING
from src.structs.structs import LogUnit
if TYPE_CHECKING:
    from src.graph.state import InterviewState
import logging 
import sys
from config import LOKI_ENDPOINT
from logging_loki import Lokihandler



handler = Lokihandler(
    url=LOKI_ENDPOINT, 
    tags={"application": "my-python-app"},
    version="1",
)

logger = logging.getLogger('agents')
stderr_handler = logging.StreamHandler(sys.stderr)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Log messages
logger.info("This is an informational message", extra={"user": "admin"})
logger.warning("This is a warning message")


# лог может быть постоянной памятью
# нужно суммаризировать ответы пользователя 
class InterviewLogger:
    def __init__(self, output_path: str = "logs/interview_log.json"):
        self.current_unit = None
        self.output_path = output_path
        self.session_start = datetime.now().isoformat()
        self.session_end: str | None = None
        
        dir_path = os.path.dirname(output_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
    
    def log_agent_action(self, role: str, event: str, info: str):
        logger.info(f"{json.dumps(info)}\n")

    def update_log_unit(self, state: "InterviewState"):
        logger.info(f"created log unit checkpoint")

        self.current_unit = LogUnit(
            participant_name=state["participant_name"],
            turns=[asdict(turn) for turn in state["turns"]],
            final_feedback=state["final_feedback"]
        )
    
    def save_session(self) -> None:
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.current_unit), f, ensure_ascii=False, indent=2)
    
    def finish(self, state: "InterviewState") -> None:
        self.session_end = datetime.now().isoformat()
        self.update_log_unit(state)
        self.save_session()
    
    def __repr__(self) -> str:
        return f"InterviewLogger(output_path='{self.output_path}')"


def get_logger() -> InterviewLogger: 
    return InterviewLogger()