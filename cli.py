#!/usr/bin/env python3
"""HelloChusquis CLI wrapper."""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import main

if __name__ == "__main__":
    sys.exit(main())