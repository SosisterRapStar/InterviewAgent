from typing import Literal
from langgraph.graph import StateGraph, END
from src.graph.state import InterviewState
from src.agents.agents import Mentor, Interviewer, Manager, VibeMaster
from src.logs import InterviewLogger
from src.structs.structs import Turn, QuestionResult
from dataclasses import asdict
import logging 
from src.structs.structs import MentorAnalysis, CalibrationResult
from src.spinner import get_spinner
import asyncio

log = logging.getLogger(__name__)

mentor = Mentor("Mentor")
interviewer = Interviewer("Interviewer")
vibe_dealer = VibeMaster("VibeMaster")
manager = Manager("Manager")
logger = InterviewLogger()


async def start_node(state: InterviewState) -> InterviewState:
    """Начало интервью - приветствие от интервьюера с валидацией роли."""
    logger.log_agent_action("Interviewer", "Генерация приветствия с валидацией роли", {
        "candidate": state['participant_name'],
        "position": state['position'],
        "grade": state['grade']
    })
    
    # Генерируем приветствие (с внутренней валидацией роли)
    async with get_spinner():
        greeting_result = await interviewer.generate_greeting(state)
    
    # Проверяем, существует ли роль в IT
    if not greeting_result.is_role_exists:
        logger.log_agent_action("Interviewer", "Валидация НЕ пройдена", {
            "position": state['position'],
            "grade": state['grade'],
            "reason": "Роль не относится к IT"
        })
        
        # Вывод для пользователя
        print(f"\n❌")
        print(f"🤖 Interviewer: {greeting_result.response}\n")
        
        # Останавливаем интервью
        state["is_finished"] = True
        state["stop_reason"] = "invalid_it_position"
        state["final_feedback"] = {
            "error": "Позиция не является IT профессией",
            "interviewer_message": greeting_result.response,
            "thinking": greeting_result.thinking
        }
        
        # Логируем отказ
        logger.update_log_unit(state)
        logger.save_session()
        
        return state
    
    # Роль валидна - продолжаем интервью
    logger.log_agent_action("Interviewer", "Валидация пройдена", {
        "position": state['position'],
        "is_it_role": True
    })
    

    # Вывод для пользователя
    print(f"🤖 Interviewer: {greeting_result.response}\n")
    return state


async def user_input_node(state: InterviewState) -> InterviewState:
    
    # Запрашиваем ответ от пользователя
    user_answer = input("👤 Вы: ")
    state["current_user_message"] = user_answer
    
    # Добавляем ответ пользователя в последний turn
    if state["turns"]:
        state["turns"][-1].user_message = state["current_user_message"]
    
    logger.log_agent_action("User", "Ответ получен", {
        "turn_id": state["turns"][-1].turn_id if state["turns"] else 0,
        "message_length": len(user_answer)
    })
    
    # Формируем контекст для VibeMaster
    last_ai_message = ""
    if state["turns"]:
        last_question = state["turns"][-1].agent_visible_message
        last_ai_message = last_question
    
    logger.log_agent_action("System", "Параллельный запуск VibeMaster и Mentor", {
        "turn_id": state["turns"][-1].turn_id if state["turns"] else 0
    })
    
    # Показываем анимацию во время параллельной обработки
    async with get_spinner():
        vibe_task = vibe_dealer.analyze_vibe(
            user_message=state["current_user_message"],
            conversation_context=last_ai_message
        )
        
        mentor_task = mentor.analyze_and_calibrate(state)
        
        
        vibe_analysis, (analysis, calibration, thinking) = await asyncio.gather(
            vibe_task,
            mentor_task
        )
    
    # Обрабатываем результат VibeMaster
    if state["turns"]:
        vibe_log = f"Намерение: {'хочет остановиться' if vibe_analysis.wants_to_stop else 'хочет продолжить'}\n"
        vibe_log += f"Состояние: {vibe_analysis.emotional_state}\n"
        vibe_log += f"Уверенность: {vibe_analysis.confidence_level}%\n"
        vibe_log += f"Анализ: {vibe_analysis.thinking}"
        state["turns"][-1].add_thought(f'[{vibe_dealer.name}]', f"{vibe_log}\n")
    
    logger.log_agent_action("VibeMaster", "Анализ завершён", {
        "wants_to_stop": vibe_analysis.wants_to_stop,
        "emotional_state": vibe_analysis.emotional_state,
        "confidence": vibe_analysis.confidence_level
    })
    

    if state["turns"]:
        current_turn = state["turns"][-1]
        current_turn.add_thought(f"[{mentor.name}]", f"{thinking}\n")
    
    state["observer_analysis"] = asdict(analysis)
    state["calibrator_recommendation"] = asdict(calibration)
    state["current_difficulty"] = calibration.difficulty_level
    
    # Добавляем тему если рекомендована новая
    if calibration.topic_recommendation and calibration.topic_recommendation not in state["topics_covered"]:
        state["topics_covered"].append(calibration.topic_recommendation)
    
    # Учитываем галлюцинации
    if analysis.answer_type == "hallucination":
        state["detected_hallucinations"].extend(analysis.factual_errors)
    
    # Учитываем off-topic
    if analysis.answer_type == "off_topic":
        state["off_topic_attempts"] += 1
    
    # Сохраняем результат вопроса
    if state["step_counter"] > 0:
        question_result = QuestionResult(
            topic=calibration.topic_recommendation or "общее",
            question=state["turns"][-1].agent_visible_message,
            user_answer=state["current_user_message"],
            is_correct=(analysis.answer_type in ["correct", "partial"]),
            correct_answer=analysis.correct_info if analysis.factual_errors else None,
            confidence=analysis.confidence_score / 100.0
        )
        state["question_results"].append(question_result)
    
    logger.log_agent_action("Mentor", "Анализ завершён", {
        "answer_type": analysis.answer_type,
        "difficulty": state['current_difficulty'],
        "next_topic": calibration.topic_recommendation,
        "confidence": analysis.confidence_score
    })
    
    # Если пользователь хочет остановиться
    if vibe_analysis.wants_to_stop:
        logger.log_agent_action("VibeMaster", "Обнаружено желание завершить интервью", {
            "reason": vibe_analysis.stop_reason,
            "confidence": vibe_analysis.confidence_level
        })
        
        state["is_finished"] = True
        state["stop_reason"] = f"user_stopped: {vibe_analysis.stop_reason}"
    
    # Логируем
    logger.update_log_unit(state)
    
    return state


def route_after_user_input(state: InterviewState) -> Literal["interviewer", "manager"]:
    """Определяет маршрут после ввода пользователя (теперь сразу к Interviewer, т.к. Mentor уже выполнен)."""
    if state.get("is_finished", False):
        return "manager" 
    return "interviewer"


async def interviewer_node(state: InterviewState) -> InterviewState:
    """Генерация ответа Interviewer'ом."""
    logger.log_agent_action("Interviewer", "Формулирование ответа на основе анализа Mentor", {
        "step": state.get("step_counter", 0),
        "questions_asked": state["questions_asked"]
    })
    
    # Получаем данные от Mentor
    analysis = state["observer_analysis"]
    calibration = state["calibrator_recommendation"]
    
    mentor_analysis = MentorAnalysis(**analysis) if isinstance(analysis, dict) else analysis
    calibration_result = CalibrationResult(**calibration) if isinstance(calibration, dict) else calibration
    
    # Генерируем ответ с анимацией
    async with get_spinner():
        response_result = await interviewer.generate_response(state, mentor_analysis, calibration_result)
    
    # Создаём новый turn, он же и первый turn, так как мы не считаем инициализированный turn :/ 
    state["step_counter"] += 1
    turn = Turn(
        turn_id=state["step_counter"],
        agent_visible_message=response_result.response,
        user_message="",
        internal_thoughts=f"[{interviewer.name}]: {response_result.thinking}\n"
    )
    
    state["turns"].append(turn)
    state["questions_asked"] += 1
    
    logger.log_agent_action("Interviewer", "Вопрос сгенерирован", {
        "turn_id": turn.turn_id,
        "questions_total": state["questions_asked"]
    })
    
    # Вывод для пользователя
    print(f"🤖 Interviewer: {response_result.response}\n")
    
    # Логируем
    logger.update_log_unit(state)
    
    return state


def check_finish_node(state: InterviewState) -> Literal["continue", "finish"]:
    """Проверяет условия завершения интервью."""
    
    # Условия завершения:
    MAX_QUESTIONS = 10
    
    # 1. Превышено количество вопросов
    if state["questions_asked"] >= MAX_QUESTIONS:
        logger.log_agent_action("System", "Достигнут лимит вопросов", {
            "questions_asked": state['questions_asked'],
            "max_questions": MAX_QUESTIONS
        })
        state["is_finished"] = True
        state["stop_reason"] = "questions_exhausted"
        return "finish"
    
    # 2. Слишком много галлюцинаций
    if len(state["detected_hallucinations"]) >= 5:
        logger.log_agent_action("System", "Слишком много галлюцинаций", {
            "hallucinations_count": len(state['detected_hallucinations']),
            "threshold": 5
        })
        state["is_finished"] = True
        state["stop_reason"] = "too_many_hallucinations"
        return "finish"
    
    # 3. Проверка на завершение уже установлеа (из user_input_node)
    if state.get("is_finished", False):
        return "finish"
    
    return "continue"


async def manager_node(state: InterviewState) -> InterviewState:
    """Генерация финального фидбэка."""
    logger.log_agent_action("Manager", "Генерация финального фидбэка", {
        "total_turns": len(state["turns"]),
        "questions_asked": state["questions_asked"],
        "topics_covered": len(state["topics_covered"])
    })
    
    # Генерируем фидбэк через Manager с анимацией
    async with get_spinner():
        feedback = await manager.generate_feedback(state)
    
    # Сохраняем в state
    state["final_feedback"] = asdict(feedback)
    
    logger.log_agent_action("Manager", "Фидбэк сгенерирован", {
        "grade": feedback.grade,
        "recommendation": feedback.hiring_recommendation,
        "confidence": feedback.confidence_score,
        "confirmed_skills_count": len(feedback.confirmed_skills),
        "knowledge_gaps_count": len(feedback.knowledge_gaps)
    })
    
    # Красиво выводим для пользователя
    print(f"\n{'='*60}")
    print(f"Фидбэк\n")
    print(f"Вердикт: {feedback.grade} | {feedback.hiring_recommendation}")
    print(f"Уверенность: {feedback.confidence_score}%\n")
    print(f"Подтверждённые навыки: {', '.join(feedback.confirmed_skills)}")
    print(f"Пробелы: {len(feedback.knowledge_gaps)} тем\n")
    print(f"Soft Skills:")
    print(f"Ясность: {feedback.clarity}")
    print(f"Честность: {feedback.honesty}")
    print(f"Вовлечённость: {feedback.engagement}\n")
    print(f"Рекомендации к изучению:")
    for item in feedback.roadmap:
        print(f"   • {item}")
    print(f"\n{'='*60}\n")
    
    # Финальное логирование
    logger.finish(state)
    
    return state


def build_interview_graph() -> StateGraph:
    """Строит граф интервью с параллельным выполнением VibeMaster + Mentor."""
    
    # Создаём граф
    workflow = StateGraph(InterviewState)
    
    # Добавляем узлы (Mentor теперь встроен в user_input_node)
    workflow.add_node("start", start_node)
    workflow.add_node("user_input", user_input_node)  # VibeMaster + Mentor параллельно
    workflow.add_node("interviewer", interviewer_node)
    workflow.add_node("manager", manager_node)
    
    workflow.set_entry_point("start")
    workflow.add_edge("start", "user_input")
    workflow.add_conditional_edges(
        "user_input",
        route_after_user_input,
        {
            "interviewer": "interviewer",
            "manager": "manager"
        }
    )
    
    # Условный переход после interviewer
    workflow.add_conditional_edges(
        "interviewer",
        check_finish_node,
        {
            "continue": "user_input", 
            "finish": "manager"
        }
    )
    
    # Завершение после manager
    workflow.add_edge("manager", END)
    
    return workflow


def create_initial_state(
    participant_name: str,
    position: str,
    grade: str,
    experience: str
) -> InterviewState:
    """Создаёт начальное состояние интервью."""
    return InterviewState(
        participant_name=participant_name,
        step_counter=0,
        position=position,
        grade=grade,
        experience=experience,
        turns=[],
        conversation_history=[],
        current_user_message="",
        current_difficulty=1,  # Начинаем c легкой сложности
        questions_asked=0,
        topics_covered=[],
        question_results=[],
        detected_hallucinations=[],
        off_topic_attempts=0,
        observer_analysis="",
        calibrator_recommendation="",
        final_feedback=None,
        is_finished=False,
        stop_reason=""
    )

