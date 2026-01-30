from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class UserIntentSchema(BaseModel):
    """Схема для определения намерений пользователя (VibeMaster)."""
    thinking: str = Field(
        description="Детальный анализ по 6 пунктам: что сказал → прямые сигналы → косвенные сигналы → эмоции → что НЕ остановка → итоговое решение"
    )
    wants_to_stop: bool = Field(
        description="Хочет ли пользователь завершить интервью (true/false)"
    )
    stop_reason: Optional[str] = Field(
        default=None,
        description="Причина завершения: tired/not_ready/too_difficult/no_time/technical_issues/other"
    )
    emotional_state: str = Field(
        default="comfortable",
        description="Эмоциональное состояние: comfortable/stressed/overwhelmed/confused/tired"
    )
    confidence_level: int = Field(
        default=80,
        ge=0, le=100,
        description="Уверенность в определении намерения (0-100%)"
    )


class MentorAnalysisSchema(BaseModel):
    thinking: str = Field(
        description="Пошаговые рассуждения: 1) Что сказал кандидат? 2) Правильно ли это? 3) Соответствует ли уровню? 4) Какая сложность нужна?"
    )
    answer_type: Literal["correct", "partial", "incorrect", "hallucination", "off_topic", "counter_question"] = Field(
        description="Тип ответа кандидата"
    )
    factual_errors: List[str] = Field(
        default_factory=list,
        description="Список конкретных фактических ошибок"
    )
    correct_info: str = Field(
        default="",
        description="Правильная информация если были ошибки"
    )
    confidence_score: int = Field(
        default=50,
        ge=0, le=100,
        description="Уверенность в оценке 0-100"
    )
    instruction_to_interviewer: str = Field(
        description="Конкретная инструкция интервьюеру что делать дальше"
    )
    difficulty_level: int = Field(
        default=3,
        ge=1, le=5,
        description="Уровень сложности следующего вопроса 1-5"
    )
    topic_recommendation: str = Field(
        description="Рекомендуемая тема следующего вопроса"
    )
    should_give_hint: bool = Field(
        default=False,
        description="Нужна ли подсказка кандидату"
    )

class InterviewerGreetingSchema(BaseModel):
    """Схема для приветствия с валидацией роли."""
    thinking: str = Field(
        description="Пошаговые рассуждения: 1) Валидация роли и грейда 2) Существует ли такая роль в IT 3) Выбор первого вопроса 4) Формулировка приветствия"
    )
    response: str = Field(
        description="Текст сообщения для кандидата (приветствие + вопрос ИЛИ объяснение почему не IT)"
    )
    is_role_exists: bool = Field(
        description="Существует ли указанная роль в IT сфере (true/false). False если роль не относится к IT или не существует."
    )


class InterviewerResponseSchema(BaseModel):
    """Схема для обычных ответов интервьюера (без валидации роли)."""
    thinking: str = Field(
        description="Пошаговые рассуждения: 1) Что сказал Mentor? 2) Как отреагировать? 3) Какой следующий вопрос?"
    )
    response: str = Field(
        description="Текст реакции и/или следующего вопроса для кандидата"
    )


class KnowledgeGap(BaseModel):
    topic: str = Field(description="Тема")
    question: str = Field(description="Вопрос на котором ошибся")
    correct_answer: str = Field(description="Правильный ответ")

# как хранить ответы юзера, в контексте? 
class FinalFeedbackSchema(BaseModel):    
    thinking: str = Field(
        description="Анализ: 1) Общее впечатление 2) Сильные стороны 3) Слабые стороны 4) Итоговая оценка"
    )
    grade: str = Field(
        description="Реальный уровень кандидата (например: Trainee, Below Junior, Junior, Junior+, Middle, Middle+, Senior, Senior+, Lead, Architect)"
    )
    hiring_recommendation: str = Field(
        description="Рекомендация по найму (например: Strong Hire, Hire, Maybe, Conditional Hire, No Hire, Strong No Hire)"
    )
    confidence_score: int = Field(
        ge=0, le=100,
        description="Уверенность в оценке 0-100"
    )
    confirmed_skills: List[str] = Field(
        default_factory=list,
        description="Подтверждённые навыки"
    )
    knowledge_gaps: List[KnowledgeGap] = Field(
        default_factory=list,
        description="Пробелы в знаниях с правильными ответами"
    )
    clarity: str = Field(
        description="Ясность изложения (например: отлично, хорошо, средне, плохо, очень плохо)"
    )
    honesty: str = Field(
        description="Честность (например: очень честный, честный, частично честный, уклончивый, нечестный)"
    )
    engagement: str = Field(
        description="Вовлечённость (например: очень высокая, высокая, средняя, низкая, очень низкая)"
    )
    
    roadmap: List[str] = Field(
        default_factory=list,
        description="Темы для изучения"
    )


class FeedbackFromInterviewer(BaseModel):
    thinking: str = Field( 
        description="Анализ: 1) Аналитика ответа от Mentor 2) Как лучше задать вопрос кандидату"
    )
    answer_to_cadidate: str = Field( 
        description="Какой вопрос задается пользователю"
    )