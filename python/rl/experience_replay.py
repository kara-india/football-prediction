from dataclasses import dataclass
import numpy as np
from collections import deque
import random
from datetime import datetime

@dataclass
class Experience:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    timestamp: datetime
    prediction_id: str

class ExperienceReplay:
    def __init__(self, max_size: int = 100_000):
        self.buffer = deque(maxlen=max_size)
    
    def add(self, experience: Experience) -> None:
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> list[Experience]:
        return random.sample(list(self.buffer), min(batch_size, len(self.buffer)))
    
    def __len__(self):
        return len(self.buffer)
