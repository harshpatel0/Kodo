import threading
from windows_toasts import InteractableWindowsToaster, Toast


class Toaster:
    def __init__(self, app_name: str = "Kodo"):
        self.toaster = InteractableWindowsToaster(app_name)
        self.toast = Toast()
        self.toast.tag = "kodo_runtime"
        self.toast.group = "agent_status"
        self.has_spawned = False
        self._lock = threading.Lock()

    def _worker_update(self, title: str, message: str):
        with self._lock:
            self.toast.text_fields = [title, message]

            if not self.has_spawned:
                self.toaster.show_toast(self.toast)
                self.has_spawned = True
            else:
                self.toaster.update_toast(self.toast)

    def _worker_teardown(self):
        with self._lock:
            if self.has_spawned:
                self.toaster.remove_toast(self.toast)
                self.has_spawned = False

    def update(self, title: str, message: str):
        threading.Thread(
            target=self._worker_update, args=(title, message), daemon=True
        ).start()

    def teardown(self):
        threading.Thread(target=self._worker_teardown, daemon=True).start()


toaster = Toaster()
