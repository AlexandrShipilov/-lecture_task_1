# deployment_script.py
# Этап внедрения: скрипт развертывания системы
import os
import shutil
import subprocess
import sys
from pathlib import Path


class DeploymentManager:
    """Менеджер развертывания системы"""

    def __init__(self, project_path: str, deploy_path: str):
        self.project_path = Path(project_path)
        self.deploy_path = Path(deploy_path)

    def validate_environment(self) -> bool:
        """Проверка окружения для развертывания"""

        # Проверяем Python
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print("Ошибка: Требуется Python 3.8 или выше")
            return False

        # Проверяем необходимые файлы
        required_files = ["task_manager.py", "system_design.py", "time_tracker.py"]
        for file in required_files:
            if not (self.project_path / file).exists():
                print(f"Ошибка: Отсутствует файл {file}")
                return False

        print("✓ Окружение проверено успешно")
        return True

    def install_dependencies(self) -> bool:
        """Установка зависимостей (если есть requirements.txt)"""

        requirements_file = self.project_path / "requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
                print("✓ Зависимости установлены успешно")
                return True
            except subprocess.CalledProcessError:
                print("Ошибка при установке зависимостей")
                return False

        print("requirements.txt не найден — зависимости не требуются")
        return True

    def deploy_files(self) -> bool:
        """Копирование файлов для развертывания"""

        try:
            # Создаем директорию для развертывания
            self.deploy_path.mkdir(parents=True, exist_ok=True)

            # Копируем все python-файлы проекта
            files_to_copy = [
                "system_design.py",
                "task_manager.py",
                "time_tracker.py",
                "test_task_system.py",
                "agile_kanban.py",
                "maintenance_monitoring.py",
            ]
            for file in files_to_copy:
                source = self.project_path / file
                if source.exists():
                    shutil.copy2(source, self.deploy_path / file)
                    print(f"✓ Скопирован {file}")

            # Создаем конфигурационный файл
            config_content = {
                "database_path": str(self.deploy_path / "tasks.db"),
                "log_level": "INFO",
                "max_users": 100
            }

            import json
            with open(self.deploy_path / "config.json", "w") as f:
                json.dump(config_content, f, indent=2)

            print("✓ Конфигурационный файл создан")
            return True

        except Exception as e:
            print(f"Ошибка при копировании файлов: {e}")
            return False

    def run_tests(self) -> bool:
        """Запуск тестов после развертывания"""

        try:
            # Запускаем тесты через unittest (стандартная библиотека Python)
            result = subprocess.run(
                [sys.executable, str(self.deploy_path / "test_task_system.py")],
                capture_output=True, text=True, cwd=str(self.deploy_path)
            )

            print(result.stdout[-500:])  # последние строки вывода тестов

            if result.returncode == 0:
                print("✓ Все тесты пройдены успешно")
                return True
            else:
                print("Некоторые тесты не пройдены:")
                print(result.stderr[-500:])
                return False

        except Exception as e:
            print(f"Ошибка при запуске тестов: {e}")
            return False

    def deploy(self) -> bool:
        """Основной процесс развертывания"""

        steps = [
            ("Проверка окружения", self.validate_environment),
            ("Установка зависимостей", self.install_dependencies),
            ("Копирование файлов", self.deploy_files),
            ("Запуск тестов", self.run_tests)
        ]

        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            if not step_func():
                print(f"Развертывание прервано на этапе: {step_name}")
                return False

        print(f"\nРазвертывание успешно завершено!")
        print(f"Система развернута в: {self.deploy_path}")
        return True


# Демонстрация процесса развертывания
if __name__ == "__main__":
    # Предполагаем, что текущая директория - это проект
    project_dir = os.getcwd()
    deploy_dir = os.path.join(project_dir, "deploy")

    deployer = DeploymentManager(project_dir, deploy_dir)
    deployer.deploy()
