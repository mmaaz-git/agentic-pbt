"""Minimal reproductions of validation bugs in aiogram.types."""

import aiogram.types as types


def reproduce_inline_keyboard_button_bugs():
    """InlineKeyboardButton violates API constraint: 'Exactly one of the optional fields must be used'"""
    
    print("=== InlineKeyboardButton Validation Bugs ===\n")
    
    # Bug 1: Accepts button with NO action fields
    button_no_action = types.InlineKeyboardButton(text="Click me")
    print(f"1. Button with NO action fields accepted:")
    print(f"   Created: {button_no_action}")
    print(f"   All actions None: {all([
        button_no_action.url is None,
        button_no_action.callback_data is None,
        button_no_action.pay is None,
        button_no_action.switch_inline_query is None
    ])}")
    
    # Bug 2: Accepts button with MULTIPLE action fields
    button_multi_action = types.InlineKeyboardButton(
        text="Multi-action",
        url="https://example.com",
        callback_data="callback",
        pay=True
    )
    print(f"\n2. Button with MULTIPLE action fields accepted:")
    print(f"   Created: {button_multi_action}")
    print(f"   Has url: {button_multi_action.url is not None}")
    print(f"   Has callback_data: {button_multi_action.callback_data is not None}")
    print(f"   Has pay: {button_multi_action.pay is not None}")
    
    # This would fail when sent to Telegram API
    serialized = button_multi_action.model_dump(exclude_none=True)
    print(f"   Serialized with multiple actions: {serialized}")
    
    return button_no_action, button_multi_action


def reproduce_negative_value_bugs():
    """Multiple types accept negative values for dimensions/offsets that should be non-negative."""
    
    print("\n=== Negative Value Validation Bugs ===\n")
    
    # Bug 1: MessageEntity accepts negative offset/length
    entity = types.MessageEntity(type="bold", offset=-10, length=-5)
    print(f"1. MessageEntity with negative offset/length:")
    print(f"   Created: {entity}")
    print(f"   offset={entity.offset}, length={entity.length}")
    
    # Bug 2: PhotoSize accepts negative dimensions
    photo = types.PhotoSize(
        file_id="photo123",
        file_unique_id="unique123",
        width=-100,
        height=-200
    )
    print(f"\n2. PhotoSize with negative dimensions:")
    print(f"   Created with width={photo.width}, height={photo.height}")
    
    # Bug 3: PollOption accepts negative voter_count
    poll_option = types.PollOption(text="Option", voter_count=-50)
    print(f"\n3. PollOption with negative voter_count:")
    print(f"   Created with voter_count={poll_option.voter_count}")
    
    # Bug 4: Video/Animation accept negative duration
    video = types.Video(
        file_id="video123",
        file_unique_id="unique123",
        width=100,
        height=100,
        duration=-30
    )
    print(f"\n4. Video with negative duration:")
    print(f"   Created with duration={video.duration}")
    
    return entity, photo, poll_option, video


def reproduce_poll_validation_bugs():
    """Poll accepts invalid configurations."""
    
    print("\n=== Poll Validation Bugs ===\n")
    
    # Bug 1: Poll accepts empty options list (API requires at least 2 options)
    empty_poll = types.Poll(
        id="poll1",
        question="Question?",
        options=[],  # Empty!
        total_voter_count=0,
        is_closed=False,
        is_anonymous=True,
        type="regular",
        allows_multiple_answers=False
    )
    print(f"1. Poll with EMPTY options list accepted:")
    print(f"   Number of options: {len(empty_poll.options)}")
    
    # Bug 2: Poll accepts single option (API requires at least 2)
    single_option_poll = types.Poll(
        id="poll2",
        question="Question?",
        options=[types.PollOption(text="Only option", voter_count=0)],
        total_voter_count=0,
        is_closed=False,
        is_anonymous=True,
        type="regular",
        allows_multiple_answers=False
    )
    print(f"\n2. Poll with SINGLE option accepted:")
    print(f"   Number of options: {len(single_option_poll.options)}")
    
    # Bug 3: Poll accepts inconsistent voter counts
    opt1 = types.PollOption(text="Option 1", voter_count=100)
    opt2 = types.PollOption(text="Option 2", voter_count=200)
    inconsistent_poll = types.Poll(
        id="poll3",
        question="Question?",
        options=[opt1, opt2],
        total_voter_count=50,  # Should be 300 for single-answer poll
        is_closed=False,
        is_anonymous=True,
        type="regular",
        allows_multiple_answers=False
    )
    print(f"\n3. Poll with inconsistent voter counts:")
    print(f"   Total voter count: {inconsistent_poll.total_voter_count}")
    print(f"   Sum of option votes: {sum(o.voter_count for o in inconsistent_poll.options)}")
    print(f"   allows_multiple_answers: {inconsistent_poll.allows_multiple_answers}")
    
    return empty_poll, single_option_poll, inconsistent_poll


def reproduce_keyboard_structure_bugs():
    """InlineKeyboardMarkup accepts invalid structures."""
    
    print("\n=== Keyboard Structure Bugs ===\n")
    
    # Bug 1: Accepts empty keyboard
    empty_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    print(f"1. Empty keyboard accepted:")
    print(f"   Number of rows: {len(empty_keyboard.inline_keyboard)}")
    
    # Bug 2: Accepts empty rows
    empty_rows_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[], [], []])
    print(f"\n2. Keyboard with empty rows accepted:")
    print(f"   Number of rows: {len(empty_rows_keyboard.inline_keyboard)}")
    print(f"   Row sizes: {[len(row) for row in empty_rows_keyboard.inline_keyboard]}")
    
    return empty_keyboard, empty_rows_keyboard


if __name__ == "__main__":
    print("Reproducing validation bugs in aiogram.types\n")
    print("=" * 50)
    
    # Run all reproductions
    reproduce_inline_keyboard_button_bugs()
    reproduce_negative_value_bugs()
    reproduce_poll_validation_bugs()
    reproduce_keyboard_structure_bugs()
    
    print("\n" + "=" * 50)
    print("\nAll bugs reproduced successfully!")
    print("\nThese validation issues could cause:")
    print("- Runtime errors when sending to Telegram API")
    print("- Unexpected behavior in production")
    print("- Silent data corruption")
    print("- API rejection of seemingly valid objects")