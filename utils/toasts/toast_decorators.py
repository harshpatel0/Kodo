from utils import toaster


def skill_installation_toast_decorator(function):
    def wrapper(*args, **kwargs):
        toaster.update("Skill Installation Mode", "Installing Skills")
