from typing import Optional
from dataclasses import dataclass


@dataclass
class Requirement:
    plugin_id: str
    version: Optional[str] = None
    official: bool = False
