"""flange_picker - detekcija tankih prirobnic iz ene kamere za bin picking."""

from .config import Config, load_config
from .pipeline import Result, process_file, process_image

__all__ = ["Config", "load_config", "Result", "process_image", "process_file"]
__version__ = "0.1.0"
