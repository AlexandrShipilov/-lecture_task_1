# test_task_system.py
# Этап тестирования: модульные тесты системы задач и модуля учёта времени
import unittest
from datetime import datetime, timedelta

from system_design import Priority, Status
from task_manager import TaskManager
from time_tracker import TimeTracker


class TestTaskSystem(unittest.TestCase):
    def setUp(self):
        """Настройка тестовой среды"""
        self.manager = TaskManager()
        self.user = self.manager.create_user("Тест User", "test@test.com")
        self.due_date = datetime.now() + timedelta(days=5)

    def test_task_creation(self):
        """Тест создания задачи"""
        task = self.manager.create_task(
            "Тестовая задача",
            "Описание тестовой задачи",
            Priority.MEDIUM,
            self.due_date
        )

        self.assertEqual(task.title, "Тестовая задача")
        self.assertEqual(task.status, Status.TODO)
        self.assertIsNone(task.assignee)

    def test_task_assignment(self):
        """Тест назначения задачи"""
        task = self.manager.create_task(
            "Назначаемая задача",
            "Должна быть назначена пользователю",
            Priority.HIGH,
            self.due_date
        )

        success = self.manager.assign_task(task.task_id, self.user.user_id)

        self.assertTrue(success)
        self.assertEqual(task.assignee.user_id, self.user.user_id)
        self.assertEqual(task.status, Status.IN_PROGRESS)

    def test_overdue_detection(self):
        """Тест обнаружения просроченных задач"""
        past_date = datetime.now() - timedelta(days=1)
        overdue_task = self.manager.create_task(
            "Просроченная задача",
            "Должна быть обнаружена как просроченная",
            Priority.LOW,
            past_date
        )

        overdue_tasks = self.manager.get_overdue_tasks()
        self.assertIn(overdue_task, overdue_tasks)

    def test_user_tasks_retrieval(self):
        """Тест получения задач пользователя"""
        task1 = self.manager.create_task("Задача 1", "Описание 1", Priority.MEDIUM, self.due_date)
        task2 = self.manager.create_task("Задача 2", "Описание 2", Priority.LOW, self.due_date)

        self.manager.assign_task(task1.task_id, self.user.user_id)
        self.manager.assign_task(task2.task_id, self.user.user_id)

        user_tasks = self.manager.get_user_tasks(self.user.user_id)
        self.assertEqual(len(user_tasks), 2)

    def test_report_generation(self):
        """Тест генерации отчета"""
        for i in range(3):
            self.manager.create_task(
                f"Задача {i}",
                f"Описание {i}",
                Priority.MEDIUM,
                self.due_date
            )

        report = self.manager.generate_report()

        self.assertEqual(report["total_tasks"], 3)
        self.assertEqual(report["status_distribution"]["To Do"], 3)


class TestTimeTracker(unittest.TestCase):
    """Тесты модуля учёта времени (практическое задание)"""

    def setUp(self):
        self.manager = TaskManager()
        self.tracker = TimeTracker(self.manager)
        self.task = self.manager.create_task("Задача с таймером", "Описание",
                                             Priority.HIGH,
                                             datetime.now() + timedelta(days=5))

    def _work(self, task_id, duration):
        """Имитация работы над задачей заданную длительность без реального ожидания"""
        self.tracker.start_timer(task_id)
        self.tracker.active_timers[task_id].start_time -= duration
        self.tracker.stop_timer(task_id)

    def test_start_timer(self):
        """Тест запуска таймера"""
        self.assertTrue(self.tracker.start_timer(self.task.task_id))
        self.assertTrue(self.tracker.is_running(self.task.task_id))

    def test_start_timer_twice_fails(self):
        """Нельзя запустить второй таймер для задачи с работающим таймером"""
        self.tracker.start_timer(self.task.task_id)
        self.assertFalse(self.tracker.start_timer(self.task.task_id))

    def test_start_timer_unknown_task(self):
        """Таймер нельзя запустить для несуществующей задачи"""
        self.assertFalse(self.tracker.start_timer(999))

    def test_stop_timer(self):
        """Тест остановки таймера"""
        self.tracker.start_timer(self.task.task_id)
        self.assertTrue(self.tracker.stop_timer(self.task.task_id))
        self.assertFalse(self.tracker.is_running(self.task.task_id))

    def test_stop_timer_not_running(self):
        """Нельзя остановить таймер, который не запущен"""
        self.assertFalse(self.tracker.stop_timer(self.task.task_id))

    def test_time_accumulates_over_sessions(self):
        """Общее время складывается из нескольких сеансов работы"""
        self._work(self.task.task_id, timedelta(hours=1))
        self._work(self.task.task_id, timedelta(hours=1))

        spent = self.tracker.get_task_time(self.task.task_id)
        self.assertAlmostEqual(spent.total_seconds(), 7200, delta=1)

    def test_running_timer_counts_time(self):
        """Идущий таймер тоже учитывается в суммарном времени"""
        self.tracker.start_timer(self.task.task_id)
        self.tracker.active_timers[self.task.task_id].start_time -= timedelta(minutes=30)

        spent = self.tracker.get_task_time(self.task.task_id)
        self.assertGreaterEqual(spent, timedelta(minutes=30))

    def test_total_time_and_report(self):
        """Тест общего времени и отчёта по времени"""
        self._work(self.task.task_id, timedelta(hours=1, minutes=30))

        report = self.tracker.generate_report()

        self.assertEqual(len(report["tasks"]), 1)
        self.assertEqual(report["tasks"][0]["title"], "Задача с таймером")
        self.assertAlmostEqual(report["tasks"][0]["time_spent_seconds"], 5400, delta=1)
        self.assertAlmostEqual(report["total_time_seconds"], 5400, delta=1)


# Запуск тестов
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTaskSystem)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTimeTracker))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\nРезультаты тестирования:")
    print(f"Пройдено тестов: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалено тестов: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
