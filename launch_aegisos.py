#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher for PyInstaller standalone build."""
import sys
import os

# Ensure package imports work from current dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aegisos.main import run

if __name__ == "__main__":
    run()