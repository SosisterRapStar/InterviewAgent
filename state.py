from typing import TypedDict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Turn:
    turn_id: int
    user_message: str
    agent_visible_message: str
    internal_thoughts: str  # Скрытая рефлексия
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass  
class QuestionResult:
    topic: str
    question: str
    user_answer: str
    is_correct: bool
    correct_answer: Optional[str] = None  # Заполняется если is_correct=False
    confidence: float = 0.0

class InterviewState(TypedDict):
    participant_name: str

    # Если эти данные юзер дает в JSON то заполним их сразу
    # Если нет - то попросим на первом узле графа достать из промпта пользователя его ожидаемые позиции
    position: str
    grade: str
    experience: str
    
    # История диалога
    turns: List[Turn]
    conversation_history: List[dict]  # Формат LangChain messages
    
    # Метрики
    current_difficulty: int  # 1-5
    questions_asked: int
    topics_covered: List[str]
    
    # Результаты (для финального фидбэка)
    question_results: List[QuestionResult]
    detected_hallucinations: List[str]
    off_topic_attempts: int
    
    # Внутренние данные между агентами
    observer_analysis: str
    calibrator_recommendation: str
    
    # Флаги
    is_finished: bool
    stop_reason: str  # "user_stopped" / "questions_exhausted"