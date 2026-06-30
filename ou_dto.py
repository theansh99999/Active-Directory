from dataclasses import dataclass
from typing import List, Optional

@dataclass
class OUNodeDTO:
    id: int
    name: str
    description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    children: List['OUNodeDTO']

@dataclass
class OUObjectsDTO:
    users: List[dict]
    groups: List[dict]
    computers: List[dict]
    children: List[dict]
