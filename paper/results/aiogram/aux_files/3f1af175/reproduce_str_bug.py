#!/usr/bin/env python3
"""Minimal reproduction of str() behavior bug in aiogram enums"""

from aiogram.enums import ChatType


def main():
    # Create an enum member
    chat_type = ChatType.PRIVATE
    
    # The enum claims to be a string and equals "private"
    assert isinstance(chat_type, str)
    assert chat_type == "private"
    
    # But str() doesn't return "private"
    result = str(chat_type)
    print(f"str(ChatType.PRIVATE) = {result!r}")
    
    # This should be "private" but is "ChatType.PRIVATE"
    assert result == "private", f"Expected 'private', got {result!r}"


if __name__ == "__main__":
    main()