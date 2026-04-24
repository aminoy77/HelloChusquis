import json
import time
from pathlib import Path
from typing import Any


class CronJob:
    """Schedule recurring tasks."""

    def __init__(self, name: str, interval: int, action: str, params: dict = None):
        self.name = name
        self.interval = interval  # seconds
        self.action = action
        self.params = params or {}
        self.last_run = 0

    def should_run(self) -> bool:
        return time.time() - self.last_run >= self.interval

    def mark_run(self):
        self.last_run = time.time()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "interval": self.interval,
            "action": self.action,
            "params": self.params,
            "last_run": self.last_run
        }


class CronScheduler:
    """Manage scheduled tasks."""

    def __init__(self):
        self.jobs: list[CronJob] = []
        self.file = Path.home() / ".hellochusquis" / "cron.json"
        self.load()

    def add(self, name: str, interval: int, action: str, params: dict = None):
        job = CronJob(name, interval, action, params)
        self.jobs.append(job)
        self.save()

    def remove(self, name: str):
        self.jobs = [j for j in self.jobs if j.name != name]
        self.save()

    def get_pending(self) -> list[CronJob]:
        return [j for j in self.jobs if j.should_run()]

    def run_pending(self, agent) -> list[str]:
        results = []
        for job in self.get_pending():
            job.mark_run()
            try:
                result = agent.run(job.action, job.params)
                results.append(f"{job.name}: {result}")
            except Exception as e:
                results.append(f"{job.name}: Error - {e}")
        return results

    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps([j.to_dict() for j in self.jobs], indent=2))

    def load(self):
        if self.file.exists():
            data = json.loads(self.file.read_text())
            for j in data:
                job = CronJob(j["name"], j["interval"], j["action"], j.get("params"))
                job.last_run = j.get("last_run", 0)
                self.jobs.append(job)


def get_scheduler() -> CronScheduler:
    return CronScheduler()