# time_tracker.py
# Практическое задание (пункт 5): модуль учёта времени для системы управления задачами.
#
# Требования:
#   1. Старт/остановка таймера для задачи
#   2. Учёт общего затраченного времени
#   3. Генерация отчётов по времени
#   4. Интеграция с существующей системой задач (TaskManager)
#
# Также этот файл — главный: при запуске он последовательно вызывает
# демонстрации всех этапов разработки из остальных файлов проекта.
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from system_design import Priority
from task_manager import TaskManager


class TimeEntry:
    """Одна запись о работе над задачей (интервал времени)"""

    def __init__(self, task_id: int, start_time: datetime):
        self.task_id = task_id
        self.start_time = start_time
        self.end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[timedelta]:
        """Длительность записи; None, если таймер ещё идёт"""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time


def format_duration(td: timedelta) -> str:
    """Форматирует timedelta в читаемый вид, например '2 ч 30 мин'"""
    total_minutes = int(td.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


class TimeTracker:
    """Учёт времени, затраченного на задачи (интегрируется с TaskManager)"""

    def __init__(self, manager: TaskManager):
        self.manager = manager                      # существующая система задач
        self.entries: List[TimeEntry] = []          # все записи о работе
        self.active_timers: Dict[int, TimeEntry] = {}  # task_id -> идущий таймер

    # --- Требование 1: старт/остановка таймера ---

    def start_timer(self, task_id: int) -> bool:
        """Запуск таймера для задачи.
        Возвращает False, если задачи нет или таймер уже запущен."""
        if task_id not in self.manager.tasks:
            return False
        if task_id in self.active_timers:
            return False
        entry = TimeEntry(task_id, datetime.now())
        self.entries.append(entry)
        self.active_timers[task_id] = entry
        return True

    def stop_timer(self, task_id: int) -> bool:
        """Остановка таймера задачи.
        Возвращает False, если таймер не был запущен."""
        entry = self.active_timers.pop(task_id, None)
        if entry is None:
            return False
        entry.end_time = datetime.now()
        return True

    def is_running(self, task_id: int) -> bool:
        """Идёт ли сейчас таймер для задачи"""
        return task_id in self.active_timers

    # --- Требование 2: общее затраченное время ---

    def get_task_time(self, task_id: int) -> timedelta:
        """Суммарное время по одной задаче (включая ещё идущий таймер)"""
        total = timedelta()
        for entry in self.entries:
            if entry.task_id != task_id:
                continue
            if entry.duration is not None:
                total += entry.duration
            else:  # таймер ещё идёт — считаем до текущего момента
                total += datetime.now() - entry.start_time
        return total

    def get_total_time(self) -> timedelta:
        """Общее время по всем задачам"""
        total = timedelta()
        for task_id in self.manager.tasks:
            total += self.get_task_time(task_id)
        return total

    # --- Требование 3: отчёты по времени ---

    def generate_report(self) -> Dict:
        """Отчёт по затраченному времени (словарь, можно превратить в JSON)"""
        tasks_report = []
        for task_id, task in self.manager.tasks.items():
            spent = self.get_task_time(task_id)
            tasks_report.append({
                "task_id": task_id,
                "title": task.title,
                "status": task.status.value,
                "time_spent_seconds": int(spent.total_seconds()),
                "time_spent": format_duration(spent),
            })

        # Сортируем: самые затратные задачи первыми
        tasks_report.sort(key=lambda t: t["time_spent_seconds"], reverse=True)

        return {
            "total_time_seconds": int(self.get_total_time().total_seconds()),
            "total_time": format_duration(self.get_total_time()),
            "tasks": tasks_report,
            "report_generated_at": datetime.now().isoformat(),
        }

    def print_report(self):
        """Вывод отчёта в консоль в читаемом виде"""
        report = self.generate_report()
        print(f"\nОтчёт по времени (всего: {report['total_time']}):")
        for t in report["tasks"]:
            print(f"  - {t['title']} [{t['status']}]: {t['time_spent']}")


# --- Демонстрация работы модуля ---
def demo_time_tracking():
    # Создаём систему задач
    manager = TaskManager()
    user = manager.create_user("Алексей Кодлов", "alexey@company.com")

    task1 = manager.create_task("Разработать REST API",
                                "Создать API для управления задачами",
                                Priority.HIGH,
                                datetime.now() + timedelta(days=14))
    task2 = manager.create_task("Написать unit-тесты",
                                "Покрыть код модульными тестами",
                                Priority.MEDIUM,
                                datetime.now() + timedelta(days=7))
    manager.assign_task(task1.task_id, user.user_id)
    manager.assign_task(task2.task_id, user.user_id)

    # Подключаем модуль учёта времени (интеграция)
    tracker = TimeTracker(manager)

    # Работа над задачей 1: один сеанс 2 ч 15 мин.
    # В реальной системе здесь просто шло бы время;
    # для демонстрации сдвигаем время старта назад вручную.
    tracker.start_timer(task1.task_id)
    tracker.active_timers[task1.task_id].start_time -= timedelta(hours=2, minutes=15)
    tracker.stop_timer(task1.task_id)

    # Работа над задачей 2: два сеанса — 45 мин и 30 мин
    for minutes in (45, 30):
        tracker.start_timer(task2.task_id)
        tracker.active_timers[task2.task_id].start_time -= timedelta(minutes=minutes)
        tracker.stop_timer(task2.task_id)

    # Отчёт по времени
    tracker.print_report()
    print("\nJSON-отчёт:")
    print(json.dumps(tracker.generate_report(), indent=2, ensure_ascii=False))


# --- Главный запуск: все этапы разработки из всех файлов проекта ---
def run_all_demos():
    print("=" * 60)
    print("СИСТЕМА УПРАВЛЕНИЯ ЗАДАЧАМИ: ВСЕ ЭТАПЫ РАЗРАБОТКИ")
    print("=" * 60)

    # [1] Сбор и анализ требований (модуль выполняется при импорте)
    print("\n[1] Сбор и анализ требований (requirements_analysis.py)")
    import requirements_analysis

    # [2] Проектирование системы
    print("\n[2] Проектирование системы (system_design.py)")
    from system_design import demonstrate_design
    demonstrate_design()

    # [3] Реализация: менеджер задач
    print("\n[3] Реализация: менеджер задач (task_manager.py)")
    from task_manager import demo_implementation
    demo_implementation()

    # [4] Практическое задание: модуль учёта времени
    print("\n[4] Модуль учёта времени (time_tracker.py) — практическое задание")
    demo_time_tracking()

    # [5] Agile: канбан-доска
    print("\n[5] Agile: канбан-доска (agile_kanban.py)")
    from agile_kanban import demo_kanban
    demo_kanban()

    # [6] Сопровождение и мониторинг
    print("\n[6] Сопровождение и мониторинг (maintenance_monitoring.py)")
    from maintenance_monitoring import demo_maintenance
    demo_maintenance()

    # [7] Внедрение и развёртывание
    print("\n[7] Внедрение и развёртывание (deployment_script.py)")
    from deployment_script import DeploymentManager
    project_dir = os.path.dirname(os.path.abspath(__file__))
    deploy_dir = os.path.join(project_dir, "deploy")
    DeploymentManager(project_dir, deploy_dir).deploy()

    print("\n" + "=" * 60)
    print("ВСЕ ЭТАПЫ ВЫПОЛНЕНЫ УСПЕШНО")
    print("=" * 60)


if __name__ == "__main__":
    run_all_demos()
