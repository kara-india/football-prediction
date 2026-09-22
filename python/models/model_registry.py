from typing import Any
import uuid

class ModelVersion:
    def __init__(self, id: str, model: Any, metrics: dict, status: str):
        self.id = id
        self.model = model
        self.metrics = metrics
        self.status = status

class ModelRegistry:
    STATUS_CHAMPION = 'champion'
    STATUS_CHALLENGER = 'challenger'
    STATUS_RETIRED = 'retired'
    
    def __init__(self):
        self.models = {} 
        
    def get_champion(self, model_name: str) -> ModelVersion | None:
        versions = self.models.get(model_name, [])
        for v in versions:
            if v.status == self.STATUS_CHAMPION:
                return v
        return None
        
    def register_challenger(self, model_name: str, model: Any, metrics: dict) -> str:
        version_id = str(uuid.uuid4())
        version = ModelVersion(version_id, model, metrics, self.STATUS_CHALLENGER)
        if model_name not in self.models:
            self.models[model_name] = []
        self.models[model_name].append(version)
        return version_id
        
    def promote_to_champion(self, version_id: str, validation_metrics: dict) -> bool:
        target_v = None
        target_name = None
        current_champ = None
        
        for name, versions in self.models.items():
            for v in versions:
                if v.id == version_id:
                    target_v = v
                    target_name = name
                if v.status == self.STATUS_CHAMPION:
                    current_champ = v
                    
            if target_v:
                break
                
        if not target_v:
            return False
            
        if not current_champ:
            target_v.status = self.STATUS_CHAMPION
            target_v.metrics = validation_metrics
            return True
            
        cur_brier = current_champ.metrics.get('brier_score', float('inf'))
        new_brier = validation_metrics.get('brier_score', float('inf'))
        
        cur_ll = current_champ.metrics.get('log_loss', float('inf'))
        new_ll = validation_metrics.get('log_loss', float('inf'))
        
        if new_brier < cur_brier and new_ll < cur_ll:
            current_champ.status = self.STATUS_RETIRED
            target_v.status = self.STATUS_CHAMPION
            target_v.metrics = validation_metrics
            return True
            
        return False
