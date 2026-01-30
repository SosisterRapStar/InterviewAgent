import sys
import asyncio
from src.graph.graph import build_interview_graph, create_initial_state
import logging 

logger = logging.getLogger(__name__)

async def main():
    print("Interview Multi-Agent System\n")
    
    print("Введите данные кандидата:")
    participant_name = input("Имя: ").strip()
    position = input("Позиция (например: Python Developer): ").strip()
    grade = input("Грейд (Junior/Middle/Senior): ").strip()
    experience = input("Опыт работы: ").strip()
    
    initial_state = create_initial_state(
        participant_name=participant_name,
        position=position,
        grade=grade,
        experience=experience
    )
    
    workflow = build_interview_graph()
    app = workflow.compile()
    
    try:
        final_state = await app.ainvoke(initial_state)
        
        logger.info("\nИнтервью завершено!")
        logger.info(f"Причина: {final_state['stop_reason']}")
        logger.info(f"Задано вопросов: {final_state['questions_asked']}")
        logger.info(f"Лог сохранён в: logs/interview_log.json")
        
    except KeyboardInterrupt:
        logger.info("\n\nИнтервью прервано пользователем")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

