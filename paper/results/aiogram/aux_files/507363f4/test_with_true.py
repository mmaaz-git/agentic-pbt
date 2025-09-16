"""Test what happens when one value is True."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiogram_env/lib/python3.13/site-packages')

from aiogram.client.default import DefaultBotProperties

# Test with one True value
props = DefaultBotProperties(
    link_preview_is_disabled=True,
    link_preview_prefer_small_media=False,
    link_preview_prefer_large_media=False,
    link_preview_show_above_text=False
)

print(f"With one True - link_preview created: {props.link_preview is not None}")
if props.link_preview:
    print(f"  is_disabled: {props.link_preview.is_disabled}")
    print(f"  prefer_small_media: {props.link_preview.prefer_small_media}")
    print(f"  prefer_large_media: {props.link_preview.prefer_large_media}")
    print(f"  show_above_text: {props.link_preview.show_above_text}")