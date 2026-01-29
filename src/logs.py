import json
import os
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING
from structs.structs import LogUnit
if TYPE_CHECKING:
    from src.graph.state import InterviewState


class InterviewLogger:
    def __init__(self, output_path: str = "logs/interview_log.json"):
        self.output_path = output_path
        self.session_start = datetime.now().isoformat()
        self.session_end: str | None = None
        
        dir_path = os.path.dirname(output_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
    
    def save(self, state: "InterviewState") -> None:
        """Сохраняет InterviewState в JSON файл."""
        
        newLogUnit = LogUnit(
            participant_name=state["participant_name"],
            turns=[asdict(turn) for turn in state["turns"]],
            final_feedback=state["final_feedback"]
        )

        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(newLogUnit), f, ensure_ascii=False, indent=2)
    
    def finish(self, state: "InterviewState") -> None:
        """Завершает сессию и сохраняет финальный лог."""
        self.session_end = datetime.now().isoformat()
        self.save(state)
    
    def __repr__(self) -> str:
        return f"InterviewLogger(output_path='{self.output_path}')"


def get_logger() -> InterviewLogger: 
    return InterviewLogger()