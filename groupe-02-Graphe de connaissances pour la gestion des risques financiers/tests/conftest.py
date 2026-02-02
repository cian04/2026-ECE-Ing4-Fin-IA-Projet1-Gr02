"""
Configuration pytest pour les tests
"""

import sys
from pathlib import Path

# Ajouter src au path pour tous les tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
