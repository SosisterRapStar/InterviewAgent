"""Точка входа в Interview Coach систему."""
import sys
from src.graph.graph import build_interview_graph, create_initial_state


def main():
    """Главная функция запуска интервью."""
    
    print("🎓 Interview Coach - Multi-Agent System\n")
    
    # Получаем данные кандидата
    print("Введите данные кандидата:")
    participant_name = input("Имя: ").strip() or "Иван Иванов"
    position = input("Позиция (например: Python Developer): ").strip() or "Python Developer"
    grade = input("Грейд (Junior/Middle/Senior): ").strip() or "Middle"
    experience = input("Опыт работы: ").strip() or "2 года коммерческой разработки"
    
    print("\n" + "="*60)
    print("Начинаем интервью!")
    print("Для завершения введите: 'стоп' или 'finish'")
    print("="*60 + "\n")
    
    # Создаём начальное состояние
    initial_state = create_initial_state(
        participant_name=participant_name,
        position=position,
        grade=grade,
        experience=experience
    )
    
    # Строим граф
    workflow = build_interview_graph()
    app = workflow.compile()
    
    try:
        # Запускаем граф
        final_state = app.invoke(initial_state)
        
        print("\n✅ Интервью завершено!")
        print(f"Причина: {final_state['stop_reason']}")
        print(f"Задано вопросов: {final_state['questions_asked']}")
        print(f"Лог сохранён в: logs/interview_log.json")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Интервью прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

