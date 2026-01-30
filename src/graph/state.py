from typing import TypedDict, List, Optional
from src.structs.structs import Turn, QuestionResult


class InterviewState(TypedDict):
    participant_name: str

    step_counter: int 
    position: str
    grade: str # только изначальный грейд
    experience: str
    
    turns: List[Turn]
    conversation_history: List[dict]
    current_user_message: str
    
    current_difficulty: int
    questions_asked: int
    topics_covered: List[str]
    
    question_results: List[QuestionResult]
    detected_hallucinations: List[str]
    off_topic_attempts: int
    
    observer_analysis: str
    calibrator_recommendation: str
    
    final_feedback: Optional[str]
    
    is_finished: bool
    stop_reason: str