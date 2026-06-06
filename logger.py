from datetime import datetime


def log_info(msg):
    print(f"[INFO] {datetime.now()} | {msg}")


def log_error(msg):
    print(f"[ERROR] {datetime.now()} | {msg}")