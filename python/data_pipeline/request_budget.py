import json
import os
from datetime import datetime

class RequestBudgetManager:
    def __init__(self, storage_path: str = "request_budget.json"):
        self.storage_path = storage_path
        self.budgets = {
            "api_football": {"daily_limit": 100, "used": 0, "last_reset": datetime.now().date().isoformat()},
        }
        self.priorities = ["P0", "P1", "P2", "P3"]
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.budgets.update(data)
                self._check_reset()

    def _save(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.budgets, f)

    def _check_reset(self):
        today = datetime.now().date().isoformat()
        for provider, budget in self.budgets.items():
            if budget.get("last_reset") != today:
                budget["used"] = 0
                budget["last_reset"] = today
        self._save()

    def reset_daily_budget(self):
        today = datetime.now().date().isoformat()
        for budget in self.budgets.values():
            budget["used"] = 0
            budget["last_reset"] = today
        self._save()

    def can_make_request(self, provider: str, priority: str, cost: int = 1) -> bool:
        self._check_reset()
        if provider not in self.budgets:
            return True # Unlimited or unmanaged
        
        budget = self.budgets[provider]
        remaining = budget["daily_limit"] - budget["used"]
        
        if remaining < cost:
            return False
            
        # P3 shouldn't deplete budget below 20%
        if priority == "P3" and (remaining - cost) < (budget["daily_limit"] * 0.2):
            return False
        # P2 shouldn't deplete budget below 10%
        if priority == "P2" and (remaining - cost) < (budget["daily_limit"] * 0.1):
            return False
            
        return True

    def record_request(self, provider: str, priority: str, endpoint: str, cost: int = 1):
        if provider in self.budgets:
            self.budgets[provider]["used"] += cost
            self._save()
            
    def get_remaining(self, provider: str) -> dict:
        self._check_reset()
        if provider in self.budgets:
            budget = self.budgets[provider]
            return {"remaining": budget["daily_limit"] - budget["used"], "limit": budget["daily_limit"]}
        return {}
