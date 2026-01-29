from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Turn:
    turn_id: int
    agent_visible_message: str  # Сообщение агента пользователю
    user_message: str = ""  # Ответ пользователя (заполняется после)
    internal_thoughts: str = ""  # Скрытая рефлексия агентов
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_thought(self, agent_name: str, thought: str) -> None:
        # здесь будем добавлять мысли 
        # возиожно лучше сделать так чтобы класс не изменял сам себя и вообще заморозить этот класс
        # нет времени на это
        if self.internal_thoughts:
            self.internal_thoughts += f"\n[{agent_name}]: {thought}"
        else:
            self.internal_thoughts = f"[{agent_name}]: {thought}"

@dataclass  
class QuestionResult:
    topic: str
    question: str
    user_answer: str
    is_correct: bool
    correct_answer: Optional[str] = None  # Заполняется если is_correct=False
    confidence: float = 0.0

@dataclass 
class LogUnit:
    participant_name: str
    # session_start: str = field(default_factory=lambda: datetime.now().isoformat())
    # session_end: Optional[str] = None
    turns: List[Turn] = field(default_factory=list)
    final_feedback: Optional[Dict[str, Any]] = None
