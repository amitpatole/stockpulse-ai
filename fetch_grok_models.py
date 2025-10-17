#!/usr/bin/env python3
"""
Fetch available Grok models from xAI API
"""

import requests
import json

# List of known Grok models based on xAI documentation (October 2024)
known_grok_models = [
    'grok-2',
    'grok-2-vision-1212',
    'grok-2-latest',
    'grok-vision-beta'
]

print("Known Grok Models (October 2024):")
print("=" * 50)
for model in known_grok_models:
    print(f"  - {model}")

print("\n" + "=" * 50)
print("Note: grok-beta and grok-2-1212 are outdated")
print("Recommended to use: grok-2 or grok-2-vision-1212")
print("=" * 50)
