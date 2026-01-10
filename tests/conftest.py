"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
