from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class Note:
    """Class responsible for representing a markdown note in the users vault."""
    title: str
    content: str
    path: Path
    is_embed: bool = False
    is_moc: bool = False

    

@dataclass
class Link:
    """Class responsible for representing a link to a markdown note in the users vault."""
    title: str
    url: str
    
@dataclass
class ExportConfigs:
    """Class responsible for representing the export configurations for the users vault."""
    
    
    