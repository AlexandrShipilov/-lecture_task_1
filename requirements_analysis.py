class TaskRequirement:
    def __init__(self, description, priority, category):
        self.description = description
        self.priority = priority  # High, Medium, Low
        self.category = category  # Functional, Non-functional

    def validate(self):
        """Валидация требований"""
        if not self.description:
            raise ValueError("Требование должно иметь описание")
        return True

# Пример требований
requirements = [
    TaskRequirement("Система должна позволять создавать задачи", "High", "Functional"),
    TaskRequirement("Время отклика менее 2 секунд", "Medium", "Non-functional")
]

print("Собранные требования:")
for req in requirements:
    print(f"- {req.description} ({req.category}, {req.priority})")