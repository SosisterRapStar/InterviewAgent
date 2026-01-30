from typing import List, Literal
from pydantic import BaseModel, Field


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

class GreetingResponse(BaseModel):
    thinking: str = Field(
        description="Рассуждения: 1) Что сказал Observer? 2) Как сформулировать ответ/вопрос?"
    )
    is_role_valid: str = Field(
        description="Валидна ли роль в IT"
    )


class InterviewerResponseSchema(BaseModel):
    thinking: str = Field(
        description="Рассуждения: 1) Что сказал Observer? 2) Как сформулировать ответ/вопрос?"
    )
    response: str = Field(
        description="Текст сообщения для кандидата"
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
    grade: Literal["Junior", "Middle", "Senior"] = Field(
        description="Реальный уровень кандидата"
    )
    hiring_recommendation: Literal["Hire", "No Hire", "Strong Hire"] = Field(
        description="Рекомендация по найму"
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
    clarity: Literal["отлично", "хорошо", "средне", "плохо"] = Field(
        description="Ясность изложения"
    )
    honesty: Literal["честный", "уклончивый"] = Field(
        description="Честность"
    )
    engagement: Literal["высокая", "средняя", "низкая"] = Field(
        description="Вовлечённость"
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