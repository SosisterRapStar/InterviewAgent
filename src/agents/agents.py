from typing import TYPE_CHECKING
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.promts.mentor import get_mentor_persona, get_analyze_prompt
from src.promts.interviewer import get_interviewer_persona, get_greeting_prompt, get_response_prompt
from src.promts.manager import get_manager_persona, get_feedback_prompt
from src.promts.vibemaster import get_vibemaster_persona, get_vibe_analysis_prompt
from src.utils import get_openrouter_llm, clean_surrogate_characters
from src.structs.structs import MentorAnalysis, CalibrationResult, FinalFeedback
from src.structs.schemas import (
    MentorAnalysisSchema, 
    InterviewerGreetingSchema,
    InterviewerResponseSchema, 
    FinalFeedbackSchema, 
    UserIntentSchema
)
import re
import json
import logging 
import asyncio

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.graph.state import InterviewState

MAX_RETRIES = 3
RETRY_DELAY = 1  # секунды между попытками


class BaseAgent:
    """Базовый класс для всех агентов."""
    
    def __init__(self, name: str, llm: BaseChatModel = None):
        self.llm = llm or get_openrouter_llm()
        self.name = name


class Mentor(BaseAgent):
    """Агент-наблюдатель и калибровщик (скрытый от пользователя).
    
    Функции:
    - Анализирует ответы кандидата
    - Определяет тип ответа (correct/incorrect/hallucination/off_topic/counter_question)
    - Выявляет фактические ошибки
    - Калибрует сложность следующего вопроса
    - Даёт инструкции Interviewer'у
    """

    def initialize_analyzer(self, state: "InterviewState"): 
        # персонализирует анализатор, задает первый
        system_prompt = get_mentor_persona(state['position'], state['grade'])
        messages = [SystemMessage(content=system_prompt)]
        messages.append(HumanMessage(content=self._get_context(state['participant_name'], state['experience'])))
        return messages

    async def analyze_and_calibrate(
        self, 
        state: "InterviewState"
    ) -> tuple[MentorAnalysis, CalibrationResult, str]:
        """Анализирует ответ и калибрует сложность через LangChain messages + structured output.
        
        Returns:
            tuple: (MentorAnalysis, CalibrationResult, thinking)
        """
        messages = [] 
        persona_prompt = get_mentor_persona(state['position'], state['grade'])
        messages.append(SystemMessage(persona_prompt))
        
        
        # История диалога (последние 3 хода)
        recent_turns = state["turns"][-3:] if state["turns"] else []
        for turn in recent_turns:
            messages.append(AIMessage(content=turn.agent_visible_message))
            if turn.user_message:
                messages.append(HumanMessage(content=turn.user_message))
        
        # Текущий ответ пользователя
        current_message = state.get("current_user_message", "")
        if current_message:
            messages.append(HumanMessage(content=current_message))
        
        # Финальный запрос с актуальными параметрами
        analyze_request = get_analyze_prompt(
            current_difficulty=state["current_difficulty"],
            topics_covered=state["topics_covered"]
        )
        messages.append(HumanMessage(content=analyze_request))
    
        try:
            structured_llm = self.llm.with_structured_output(
                MentorAnalysisSchema,
                method="json_mode"
            )
            result = await structured_llm.ainvoke(messages)
        except Exception as e:
            # Fallback: обычный вызов и ручной парсинг
            response = await self.llm.ainvoke(messages)
            
            content = response.content
            content = clean_surrogate_characters(content)  # Очищаем от суррогатных символов
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*$', '', content)
            
            # Парсим JSON
            try:
                parsed = json.loads(content)
                
                # Конвертация thinking из dict в string если LLM вернул словарь
                if isinstance(parsed.get('thinking'), dict):
                    thinking_dict = parsed['thinking']
                    parsed['thinking'] = '\n'.join([f"{k}: {v}" for k, v in thinking_dict.items()])
                
                result = MentorAnalysisSchema(**parsed)
            except json.JSONDecodeError:
                # Если JSON невалидный, пытаемся найти JSON объект в тексте
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    parsed = json.loads(json_match.group())
                    
                    # Конвертация thinking из dict в string если LLM вернул словарь
                    if isinstance(parsed.get('thinking'), dict):
                        thinking_dict = parsed['thinking']
                        parsed['thinking'] = '\n'.join([f"{k}: {v}" for k, v in thinking_dict.items()])
                    
                    result = MentorAnalysisSchema(**parsed)
                else:
                    # даем челу на интервьюере базовые рекомендации
                    result = MentorAnalysisSchema(
                        thinking="Не удалось распарсить ответ",
                        answer_type="partial",
                        factual_errors=[],
                        correct_info="",
                        confidence_score=50,
                        instruction_to_interviewer="Продолжай интервью",
                        difficulty_level=state["current_difficulty"],
                        topic_recommendation="общие вопросы",
                        should_give_hint=False
                    )
        
        # Формируем MentorAnalysis из схемы
        analysis = MentorAnalysis(
            answer_type=result.answer_type,
            factual_errors=result.factual_errors,
            correct_info=result.correct_info,
            confidence_score=result.confidence_score,
            instruction_to_interviewer=result.instruction_to_interviewer
        )
        
        # Формируем CalibrationResult из той же схемы
        calibration = CalibrationResult(
            difficulty_level=result.difficulty_level,
            topic_recommendation=result.topic_recommendation,
            should_give_hint=result.should_give_hint
        )
        
        return analysis, calibration, result.thinking


class Interviewer(BaseAgent):
    def _get_user_info(self, state: "InterviewState") -> str:
        return f"""## ИНФОРМАЦИЯ О КАНДИДАТЕ
                Имя: {state["participant_name"]}
                Позиция: {state["position"]}
                Уровень: {state["grade"]}
                Опыт: {state["experience"]}"""

    async def generate_greeting(self, state: "InterviewState") -> InterviewerGreetingSchema:
        system_prompt = get_interviewer_persona(state["position"], state["grade"])
        messages = [SystemMessage(content=system_prompt)]
        
        context = self._get_user_info(state)
        messages.append(SystemMessage(content=context))
        
        greeting_request = get_greeting_prompt(state["position"], state["grade"])
        messages.append(HumanMessage(content=greeting_request))
        
        # Используем retry логику
        for attempt in range(MAX_RETRIES):
            try:
                structured_llm = self.llm.with_structured_output(
                    InterviewerGreetingSchema,  # ← Используем схему с is_role_exists
                    method="json_mode"
                )
                result = await structured_llm.ainvoke(messages)
                return result  # Успех
                
            except Exception as e:
                logger.warning(f"Interviewer.generate_greeting попытка {attempt + 1}/{MAX_RETRIES} провалилась: {e}")
                
                # Пробуем fallback
                if attempt < MAX_RETRIES - 1:
                    try:
                        response = await self.llm.ainvoke(messages)
                        content = response.content
                        content = clean_surrogate_characters(content)  # Очищаем от суррогатных символов
                        content = re.sub(r'```json\s*', '', content)
                        content = re.sub(r'```\s*$', '', content)
                        
                        parsed = json.loads(content)
                        
                        # Конвертация thinking из dict в string если LLM вернул словарь
                        if isinstance(parsed.get('thinking'), dict):
                            thinking_dict = parsed['thinking']
                            parsed['thinking'] = '\n'.join([f"{k}: {v}" for k, v in thinking_dict.items()])
                        
                        result = InterviewerGreetingSchema(**parsed)
                        logger.info(f"Fallback парсинг успешен на попытке {attempt + 1}")
                        return result
                    except Exception as fallback_error:
                        logger.warning(f"Fallback провалился: {fallback_error}")
                        await asyncio.sleep(RETRY_DELAY)
                        continue
        
        logger.error(f"Interviewer.generate_greeting: все {MAX_RETRIES} попытки провалились")
        raise Exception(f"Failed to generate greeting after {MAX_RETRIES} attempts")

    def _get_mentor_instructions(self, mentor_analysis: MentorAnalysis, calibration: CalibrationResult) -> str: 
        return f"""Тип ответа: {mentor_analysis.answer_type}
                Фактические ошибки: {", ".join(mentor_analysis.factual_errors) or "нет"}
                Правильная информация: {mentor_analysis.correct_info or "—"}
                Что делать: {mentor_analysis.instruction_to_interviewer}

                Рекомендуемая сложность: {calibration.difficulty_level}/5
                Рекомендуемая тема: {calibration.topic_recommendation}
                Нужна подсказка: {"да" if calibration.should_give_hint else "нет"}"""
        
    async def generate_response(
        self, 
        state: "InterviewState", 
        mentor_analysis: MentorAnalysis, 
        calibration: CalibrationResult
    ) -> InterviewerResponseSchema:
        """Генерирует ответ на основе анализа Mentor (БЕЗ валидации роли)."""
        persona_prompt = get_interviewer_persona(state["position"], state["grade"])
        messages = [SystemMessage(content=persona_prompt)]
        
        recent_turns = state["turns"][-3:] if state["turns"] else []
        for turn in recent_turns:
            messages.append(AIMessage(content=turn.agent_visible_message))
            if turn.user_message:
                messages.append(HumanMessage(content=turn.user_message))
        
        mentor_instructions = self._get_mentor_instructions(mentor_analysis, calibration)
        response_request = get_response_prompt(
            mentor_instructions=mentor_instructions,
            topics_covered=state["topics_covered"]
        )
        messages.append(HumanMessage(content=response_request))
        
        # Используем retry логику
        for attempt in range(MAX_RETRIES):
            try:
                structured_llm = self.llm.with_structured_output(
                    InterviewerResponseSchema,  # ← Схема БЕЗ is_role_exists
                    method="json_mode"
                )
                result = await structured_llm.ainvoke(messages)
                logger.info(f"Interviewer.generate_response успешен")
                return result  # Успех
                
            except Exception as e:
                logger.warning(f"Interviewer.generate_response попытка {attempt + 1}/{MAX_RETRIES} провалилась: {e}")
                
                # Пробуем fallback
                if attempt < MAX_RETRIES - 1:
                    try:
                        response = await self.llm.ainvoke(messages)
                        content = response.content
                        content = clean_surrogate_characters(content)  # Очищаем от суррогатных символов
                        content = re.sub(r'```json\s*', '', content)
                        content = re.sub(r'```\s*$', '', content)
                        
                        parsed = json.loads(content)
                        
                        # Конвертация thinking из dict в string если LLM вернул словарь
                        if isinstance(parsed.get('thinking'), dict):
                            thinking_dict = parsed['thinking']
                            parsed['thinking'] = '\n'.join([f"{k}: {v}" for k, v in thinking_dict.items()])
                        
                        result = InterviewerResponseSchema(**parsed)
                        logger.info(f"Fallback парсинг успешен на попытке {attempt + 1}")
                        return result
                    except Exception as fallback_error:
                        logger.warning(f"Fallback провалился: {fallback_error}")
                        await asyncio.sleep(RETRY_DELAY)
                        continue
        
        # Все попытки провалились
        logger.error(f"Interviewer.generate_response: все {MAX_RETRIES} попытки провалились")
        raise Exception(f"Failed to generate response after {MAX_RETRIES} attempts")




class Manager(BaseAgent):
    # дублирование кода как у дибила
    # TODO: убрать дубли потом
    def _get_user_context(self, 
        name: str, 
        position: str,
        grade: str,
        exp, 
        questions_asked,
        topics,
        hallucinations,
        off_top ) -> str: 
        return f"""Кандидат: {name}
            Позиция: {position} | Грейд: {grade}
            Опыт: {exp}

            Статистика:
            - Вопросов: {questions_asked}
            - Темы: {", ".join(topics) or "—"}
            - Галлюцинаций: {len(hallucinations)}
            - Off-topic: {off_top}"""


    async def generate_feedback(self, state: "InterviewState") -> FinalFeedback:
        """Генерирует фидбэк на основе полной истории с повторными попытками."""
        system_prompt = get_manager_persona(state['position'], state['grade'])
        messages = [SystemMessage(content=system_prompt)]
        
        # Контекст о кандидате
        candidate_context = self._get_user_context(
            name=state['participant_name'],
            position=state['position'],
            grade=state['grade'],
            exp=state['experience'],
            questions_asked=state['questions_asked'],
            topics=state['topics_covered'],
            hallucinations=state['detected_hallucinations'],
            off_top=state['off_topic_attempts']
        )
        messages.append(SystemMessage(content=candidate_context))
        
        for turn in state["turns"]:
            messages.append(AIMessage(content=turn.agent_visible_message))
            if turn.user_message:
                messages.append(HumanMessage(content=turn.user_message))
        
        feedback_request = get_feedback_prompt()
        messages.append(HumanMessage(content=feedback_request))
        
        for attempt in range(MAX_RETRIES):
            try:
                structured_llm = self.llm.with_structured_output(
                    FinalFeedbackSchema,
                    method="json_mode"
                )
                result = await structured_llm.ainvoke(messages)
                
                feedback = FinalFeedback(
                    grade=result.grade,
                    hiring_recommendation=result.hiring_recommendation,
                    confidence_score=result.confidence_score,
                    confirmed_skills=result.confirmed_skills,
                    knowledge_gaps=[
                        {"topic": gap.topic, "question": gap.question, "correct_answer": gap.correct_answer}
                        for gap in result.knowledge_gaps
                    ],
                    clarity=result.clarity,
                    honesty=result.honesty,
                    engagement=result.engagement,
                    roadmap=result.roadmap
                )
                
                logger.info(f"Manager.generate_feedback успешно завершён")
                logger.debug(f"Manager thinking: {result.thinking[:200]}...")
                return feedback
                
            except Exception as e:
                logger.warning(f"Manager.generate_feedback попытка {attempt + 1}/{MAX_RETRIES} провалилась: {e}")
                
                if attempt < MAX_RETRIES - 1:
                    try:
                        response = await self.llm.ainvoke(messages)
                        content = response.content
                        content = clean_surrogate_characters(content)  # Очищаем от суррогатных символов
                        content = re.sub(r'```json\s*', '', content)
                        content = re.sub(r'```\s*$', '', content)
                        
                        parsed = json.loads(content)
                        
                        # Конвертация thinking из dict в string если LLM вернул словарь
                        if isinstance(parsed.get('thinking'), dict):
                            thinking_dict = parsed['thinking']
                            parsed['thinking'] = '\n'.join([f"{k}: {v}" for k, v in thinking_dict.items()])
                        
                        result = FinalFeedbackSchema(**parsed)
                        
                        feedback = FinalFeedback(
                            grade=result.grade,
                            hiring_recommendation=result.hiring_recommendation,
                            confidence_score=result.confidence_score,
                            confirmed_skills=result.confirmed_skills,
                            knowledge_gaps=[
                                {"topic": gap.topic, "question": gap.question, "correct_answer": gap.correct_answer}
                                for gap in result.knowledge_gaps
                            ],
                            clarity=result.clarity,
                            honesty=result.honesty,
                            engagement=result.engagement,
                            roadmap=result.roadmap
                        )
                        
                        logger.info(f"Fallback парсинг успешен на попытке {attempt + 1}")
                        return feedback
                    except Exception as fallback_error:
                        logger.warning(f"Fallback провалился: {fallback_error}")
                        await asyncio.sleep(RETRY_DELAY)
                        continue
        
        logger.error(f"Manager.generate_feedback: все {MAX_RETRIES} попытки провалились")
        raise Exception(f"Failed to generate feedback after {MAX_RETRIES} attempts")


class VibeMaster(BaseAgent): # он же вайбдиллер
    """Агент-анализатор настроения и намерений кандидата."""
    
    async def analyze_vibe(
        self, 
        user_message: str, 
        conversation_context: str = ""
    ) -> UserIntentSchema:
    
        persona_prompt = get_vibemaster_persona()
        messages = [SystemMessage(content=persona_prompt)]
        
        if conversation_context:
            messages.append(AIMessage(content=conversation_context))
        
        analysis_request = get_vibe_analysis_prompt()
        messages.append(HumanMessage(content=f"{analysis_request}\n\nОтвет кандидата: \"{user_message}\""))
        
        for attempt in range(MAX_RETRIES):
            try:
                structured_llm = self.llm.with_structured_output(
                    UserIntentSchema,
                    method="json_mode"
                )
                result = await structured_llm.ainvoke(messages)
                
                logger.info(f"VibeMaster: wants_to_stop={result.wants_to_stop}, state={result.emotional_state}")
                return result
                
            except Exception as e:
                logger.warning(f"VibeMaster.analyze_vibe попытка {attempt + 1}/{MAX_RETRIES} провалилась: {e}")
                
                if attempt < MAX_RETRIES - 1:
                    try:
                        # Fallback парсинг
                        response = await self.llm.ainvoke(messages)
                        content = response.content
                        content = clean_surrogate_characters(content)  # Очищаем от суррогатных символов
                        content = re.sub(r'```json\s*', '', content)
                        content = re.sub(r'```\s*$', '', content)
                        
                        parsed = json.loads(content)
                        
                        # Конвертация thinking из dict в string если LLM вернул словарь
                        if isinstance(parsed.get('thinking'), dict):
                            thinking_dict = parsed['thinking']
                            parsed['thinking'] = '\n'.join([f"{k}: {v}" for k, v in thinking_dict.items()])
                        
                        result = UserIntentSchema(**parsed)
                        logger.info(f"Fallback успешен на попытке {attempt + 1}")
                        return result
                    except Exception as fallback_error:
                        logger.warning(f"Fallback провалился: {fallback_error}")
                        await asyncio.sleep(RETRY_DELAY)
                        continue
        
        # Все попытки провалились - возвращаем дефолт (продолжаем интервью)
        logger.error("VibeMaster: все попытки провалились, предполагаем что кандидат хочет продолжить")
        return UserIntentSchema(
            thinking="Не удалось определить намерение, продолжаем интервью по умолчанию",
            wants_to_stop=False,
            stop_reason=None,
            emotional_state="neutral",
            confidence_level=0
        )
