from typing import TypedDict, List, Optional
from src.structs.structs import Turn, QuestionResult


class InterviewState(TypedDict):
    participant_name: str

    # Вводные данные кандидата
    position: str
    grade: str  # Junior / Middle / Senior
    experience: str
    
    # История диалога
    turns: List[Turn]
    conversation_history: List[dict]  # Формат LangChain messages
    
    # Текущее сообщение пользователя (для обработки в цикле)
    current_user_message: str
    
    # Метрики
    current_difficulty: int  # 1-5
    questions_asked: int
    topics_covered: List[str]
    
    # Результаты оценки
    question_results: List[QuestionResult]
    detected_hallucinations: List[str]
    off_topic_attempts: int
    
    # Внутренняя коммуникация между агентами
    observer_analysis: str
    calibrator_recommendation: str
    
    # Финальный фидбэк
    final_feedback: Optional[str]
    
    # Флаги состояния
    is_finished: bool
    stop_reason: str  # "user_stopped" / "questions_exhausted"