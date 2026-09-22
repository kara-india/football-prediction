import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    supabase_url: str = os.getenv('SUPABASE_URL', os.getenv('NEXT_PUBLIC_SUPABASE_URL', ''))
    supabase_key: str = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')  # server-only
    supabase_publishable_key: str = os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY', '')
    api_football_key: str = os.getenv('API_FOOTBALL_KEY', '')
    odds_api_key: str = os.getenv('ODDS_API_KEY', '')
    python_engine_port: int = int(os.getenv('PYTHON_ENGINE_PORT', '8001'))
    
    def validate_for_worker(self):
        if not self.supabase_url:
            raise ValueError('SUPABASE_URL required for workers')
        if not self.supabase_key:
            raise ValueError('SUPABASE_SERVICE_ROLE_KEY required for workers')
    
    def has_football_api(self) -> bool:
        return bool(self.api_football_key)
    
    def has_odds_api(self) -> bool:
        return bool(self.odds_api_key)

config = Config()
