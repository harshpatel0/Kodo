from settings.settings import settings
from orchestrators.autonomy_orchestrator import AutonomyOrchestrator


def run_externally(task: str):
    autonomy_orchestrator = AutonomyOrchestrator(task=task)

    if not settings.interactions.no_skill_installation_mode:
        autonomy_orchestrator.run_skill_installation_mode()
    autonomy_orchestrator.run()


if __name__ == "__main__":
    task = input("What task would you like to run?\n")
    run_externally(task=task)
