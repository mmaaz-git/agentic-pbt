"""Minimal reproduction of DefaultBotProperties bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiogram_env/lib/python3.13/site-packages')

from aiogram.client.default import DefaultBotProperties

# This should create a LinkPreviewOptions object with all False values
props = DefaultBotProperties(
    link_preview_is_disabled=False,
    link_preview_prefer_small_media=False,
    link_preview_prefer_large_media=False,
    link_preview_show_above_text=False
)

print(f"link_preview created: {props.link_preview is not None}")
print(f"link_preview value: {props.link_preview}")

# Expected: link_preview should be created with all False values
# Actual: link_preview is None