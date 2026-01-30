from typing import Literal
from langgraph.graph import StateGraph, END
from src.graph.state import InterviewState
from src.agents.agents import Mentor, Interviewer, Manager
from src.logs import InterviewLogger
from src.structs.structs import Turn, QuestionResult
from dataclasses import asdict
import logging 
from src.structs.structs import MentorAnalysis, CalibrationResult

log = logging.getLogger(__name__)

# Инициализация агентов и логгера
mentor = Mentor("Mentor")
interviewer = Interviewer("Interviewer")
manager = Manager("Manager")
logger = InterviewLogger()


# нужно как-то сделать так, чтобы ментор не был таким жестким, он сильно валит
# нужно научиться определять желания пользователя
# ментор должен уметь говорить интервьюеру, что чел несет ахинею
def start_node(state: InterviewState) -> InterviewState:
    """Начало интервью - приветствие от интервьюера."""
    print(f"\n{'='*60}")
    print(f"🎯 Начинаем техническое интервью")
    print(f"Кандидат: {state['participant_name']}")
    print(f"Позиция: {state['position']} ({state['grade']})")
    print(f"{'='*60}\n")
    
    # Генерируем приветствие
    greeting_result = interviewer.generate_greeting(state)
    
    # Создаём первый turn
    turn = Turn(
        turn_id=1,
        agent_visible_message=greeting_result.response,
        user_message="",
        internal_thoughts=f"[{interviewer.name} thinking]: {greeting_result.thinking}"
    )
    
    # Обновляем state
    state["turns"].append(turn)
    state["step_counter"] = 1
    state["questions_asked"] = 1
    
    print(f"🤖 Interviewer: {greeting_result.response}\n")
    
    # Логируем
    logger.update_log_unit(state)
    
    return state


def user_input_node(state: InterviewState) -> InterviewState:
    """Получение ответа от пользователя."""
    # Запрашиваем ответ от пользователя
    user_answer = input("👤 Вы: ")
    state["current_user_message"] = user_answer
    
    # Добавляем ответ пользователя в последний turn
    if state["turns"]:
        # обновляем последний созданный turn
        state["turns"][-1].user_message = state["current_user_message"]
    
    print(f"👤 Кандидат: {state['current_user_message']}\n")
    
    return state

# ментору нужно добавить тулзы на фактчекинг
def mentor_node(state: InterviewState) -> InterviewState:
    """Анализ ответа Mentor'ом."""
    print("🔍 Mentor анализирует ответ...")
    
    # Анализируем через Mentor
    analysis, calibration, thinking = mentor.analyze_and_calibrate(state)
    
    # Создаём новый turn для internal thoughts
    current_turn = state["turns"][-1]
    current_turn.add_thought("Mentor", thinking)
    
    # Обновляем state с результатами анализа
    state["observer_analysis"] = asdict(analysis)
    state["calibrator_recommendation"] = asdict(calibration)
    
    # Обновляем сложность
    # возможно, нужно убрать эту метрику
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
    question_result = QuestionResult(
        topic=calibration.topic_recommendation or "общее",
        question=state["turns"][-1].agent_visible_message,
        user_answer=state["current_user_message"],
        is_correct=(analysis.answer_type in ["correct", "partial"]),
        correct_answer=analysis.correct_info if analysis.factual_errors else None,
        confidence=analysis.confidence_score / 100.0
    )
    state["question_results"].append(question_result)
    
    print(f"   ✓ Тип ответа: {analysis.answer_type}")
    print(f"   ✓ Сложность: {state['current_difficulty']}/5")
    print(f"   ✓ Следующая тема: {calibration.topic_recommendation}\n")
    
    # Логируем
    logger.update_log_unit(state)
    
    return state


def interviewer_node(state: InterviewState) -> InterviewState:
    print("💬 Interviewer формулирует ответ...\n")
    
    # Получаем данные от Mentor
    analysis = state["observer_analysis"]
    calibration = state["calibrator_recommendation"]

    
    mentor_analysis = MentorAnalysis(**analysis) if isinstance(analysis, dict) else analysis
    calibration_result = CalibrationResult(**calibration) if isinstance(calibration, dict) else calibration
    
    # Генерируем ответ
    response_result = interviewer.generate_response(state, mentor_analysis, calibration_result)
    
    # Создаём новый turn
    state["step_counter"] += 1
    turn = Turn(
        turn_id=state["step_counter"],
        agent_visible_message=response_result.response,
        user_message="",
        internal_thoughts=f"[Interviewer thinking]: {response_result.thinking}"
    )
    
    state["turns"].append(turn)
    state["questions_asked"] += 1
    
    print(f"🤖 Interviewer: {response_result.response}\n")
    
    # Логируем
    logger.update_log_unit(state)
    
    return state


def check_finish_node(state: InterviewState) -> Literal["continue", "finish"]:
    """Проверяет условия завершения интервью."""
    
    # Условия завершения:
    # 1. Достигнуто максимальное количество вопросов
    MAX_QUESTIONS = 10
    
    # 2. Пользователь явно попросил завершить
    if state.get("current_user_message", "").lower() in ["стоп", "stop", "finish", "завершить"]:
        state["is_finished"] = True
        state["stop_reason"] = "user_stopped"
        return "finish"
    
    # 3. Превышено количество вопросов
    if state["questions_asked"] >= MAX_QUESTIONS:
        state["is_finished"] = True
        state["stop_reason"] = "questions_exhausted"
        return "finish"
    
    # 4. Слишком много галлюцинаций
    if len(state["detected_hallucinations"]) >= 5:
        state["is_finished"] = True
        state["stop_reason"] = "too_many_hallucinations"
        return "finish"
    
    return "continue"


def manager_node(state: InterviewState) -> InterviewState:
    """Генерация финального фидбэка."""
    print(f"\n{'='*60}")
    print("📊 Генерация финального фидбэка...")
    print(f"{'='*60}\n")
    
    # Генерируем фидбэк через Manager
    feedback = manager.generate_feedback(state)
    
    # Сохраняем в state
    state["final_feedback"] = asdict(feedback)
    
    # Красиво выводим
    print(f"📋 ФИНАЛЬНЫЙ ФИДБЭК\n")
    print(f"Вердикт: {feedback.grade} | {feedback.hiring_recommendation}")
    print(f"Уверенность: {feedback.confidence_score}%\n")
    print(f"✅ Подтверждённые навыки: {', '.join(feedback.confirmed_skills)}")
    print(f"❌ Пробелы: {len(feedback.knowledge_gaps)} тем\n")
    print(f"💬 Soft Skills:")
    print(f"   Ясность: {feedback.clarity}")
    print(f"   Честность: {feedback.honesty}")
    print(f"   Вовлечённость: {feedback.engagement}\n")
    print(f"🎓 Рекомендации к изучению:")
    for item in feedback.roadmap:
        print(f"   • {item}")
    print(f"\n{'='*60}\n")
    
    # Финальное логирование
    logger.finish(state)
    
    return state


def build_interview_graph() -> StateGraph:
    """Строит граф интервью."""
    
    # Создаём граф
    workflow = StateGraph(InterviewState)
    
    # Добавляем узлы
    workflow.add_node("start", start_node)
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("mentor", mentor_node)
    workflow.add_node("interviewer", interviewer_node)
    workflow.add_node("manager", manager_node)
    
    # Устанавливаем точку входа
    workflow.set_entry_point("start")
    
    # Связываем узлы
    workflow.add_edge("start", "user_input")
    workflow.add_edge("user_input", "mentor")
    workflow.add_edge("mentor", "interviewer")
    
    # Условный переход после interviewer
    workflow.add_conditional_edges(
        "interviewer",
        check_finish_node,
        {
            "continue": "user_input",  # Возвращаемся к вводу пользователя
            "finish": "manager"         # Идём к финальному фидбэку
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
        current_difficulty=3,  # Начинаем со средней сложности
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

