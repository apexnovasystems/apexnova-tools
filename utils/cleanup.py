import shutil
import threading
from pathlib import Path
from flask import session

def delete_user_folder(base_dir: Path, user_id: str):
    """Delete a user's temporary directory."""
    folder = base_dir / user_id
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)

def schedule_cleanup(base_dir: Path, user_id: str, delay_seconds: int = 10):
    """Schedule deletion of user folder after a short delay (e.g., after page unload)."""
    def delayed_delete():
        import time
        time.sleep(delay_seconds)
        delete_user_folder(base_dir, user_id)
    threading.Thread(target=delayed_delete, daemon=True).start()