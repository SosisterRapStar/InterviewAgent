from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

# формируют стейт
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


# единица лога
@dataclass 
class LogUnit:
    participant_name: str
    # session_start: str = field(default_factory=lambda: datetime.now().isoformat())
    # session_end: Optional[str] = None
    turns: List[Turn] = field(default_factory=list)
    final_feedback: Optional[Dict[str, Any]] = None

@dataclass 
class InterviewerAnalysis: 
    want_to_stop: str
    
# структуры для коммуникации между агентами
@dataclass
class MentorAnalysis:
    """Результат анализа ответа кандидата от Mentor."""
    answer_type: str  # correct / incorrect / partial / hallucination / off_topic / counter_question
    factual_errors: List[str] = field(default_factory=list)
    correct_info: str = ""  # правильная информация если были ошибки
    confidence_score: int = 0  # 0-100, уверенность в оценке
    instruction_to_interviewer: str = ""  # инструкция что делать дальше

@dataclass
class CalibrationResult:
    """Результат калибровки сложности от Mentor."""
    difficulty_level: int = 3  # 1-5
    topic_recommendation: str = ""  # рекомендуемая тема следующего вопроса
    should_give_hint: bool = False  # нужна ли подсказка

@dataclass
class FinalFeedback:
    """Финальный фидбэк от Manager. Manager на самом деле не совсем manager, он также проверяет и уровень на основе ответов"""
    # Вердикт
    grade: str = ""  # Junior / Middle / Senior
    hiring_recommendation: str = ""  # Hire / No Hire / Strong Hire
    confidence_score: int = 0  # 0-100
    
    # Hard Skills
    confirmed_skills: List[str] = field(default_factory=list)
    knowledge_gaps: List[Dict[str, str]] = field(default_factory=list)  # [{topic, question, correct_answer}]
    
    # Soft Skills
    clarity: str = ""  # оценка ясности изложения
    honesty: str = ""  # оценка честности
    engagement: str = ""  # оценка вовлечённости
    
    # Roadmap
    roadmap: List[str] = field(default_factory=list)  # темы для изучения

