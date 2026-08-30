#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT_IMPORT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT_IMPORT))
from server.domain_profiles import resolve_profile
from server.cross_domain_engine import preview_contract
assert resolve_profile("hair_beard")["profile_key"]=="mens_hair_beard"
assert resolve_profile("color_gray")["profile_key"]=="hair_color"
print("PASS: v0.3 men's aliases remain compatible with cross-domain core")
