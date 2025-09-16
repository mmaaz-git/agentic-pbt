"""Property-based tests for aiogram.types using Hypothesis."""

import json
from datetime import datetime, timezone

import pytest
from hypothesis import assume, given, strategies as st

import aiogram.types as types


# Strategy for creating valid text
text_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

# Strategy for creating InlineKeyboardButton action fields
action_strategy = st.one_of(
    st.builds(dict, callback_data=st.text(min_size=1, max_size=64)),
    st.builds(dict, url=st.text(min_size=1).map(lambda x: f"https://example.com/{x}")),
    st.builds(dict, switch_inline_query=st.text()),
    st.builds(dict, switch_inline_query_current_chat=st.text()),
    st.builds(dict, pay=st.just(True)),
)


@given(
    text=text_strategy,
    action=st.one_of(action_strategy, st.none())
)
def test_inline_keyboard_button_round_trip(text, action):
    """Test that InlineKeyboardButton survives serialization round-trip."""
    button_data = {"text": text}
    if action:
        button_data.update(action)
    
    button = types.InlineKeyboardButton(**button_data)
    
    # Test model_dump round-trip
    dumped = button.model_dump()
    reconstructed = types.InlineKeyboardButton(**dumped)
    assert button == reconstructed
    
    # Test JSON round-trip
    json_str = button.model_dump_json()
    parsed = json.loads(json_str)
    reconstructed_json = types.InlineKeyboardButton(**parsed)
    assert button == reconstructed_json


@given(
    type_=st.sampled_from(['bold', 'italic', 'code', 'url', 'mention', 'hashtag']),
    offset=st.integers(min_value=-1000, max_value=1000),
    length=st.integers(min_value=-1000, max_value=1000)
)
def test_message_entity_accepts_negative_values(type_, offset, length):
    """Test that MessageEntity incorrectly accepts negative offset/length values."""
    # This should arguably fail for negative values, but it doesn't
    entity = types.MessageEntity(type=type_, offset=offset, length=length)
    
    # The entity is created successfully even with negative values
    assert entity.offset == offset
    assert entity.length == length
    
    # Check if it survives serialization
    dumped = entity.model_dump()
    reconstructed = types.MessageEntity(**dumped)
    assert entity == reconstructed


@given(
    width=st.integers(min_value=-10000, max_value=10000),
    height=st.integers(min_value=-10000, max_value=10000)
)
def test_photo_size_accepts_negative_dimensions(width, height):
    """Test that PhotoSize incorrectly accepts negative width/height."""
    photo = types.PhotoSize(
        file_id="test_id",
        file_unique_id="unique_id",
        width=width,
        height=height
    )
    
    # PhotoSize accepts any integer for dimensions
    assert photo.width == width
    assert photo.height == height


@given(text=text_strategy)
def test_inline_keyboard_button_without_action(text):
    """Test that InlineKeyboardButton accepts buttons with no action fields.
    
    According to API docs: 'Exactly one of the optional fields must be used'
    """
    # Create button with only text (no action)
    button = types.InlineKeyboardButton(text=text)
    
    # Check all action fields are None
    action_fields = [
        button.url,
        button.callback_data,
        button.switch_inline_query,
        button.switch_inline_query_current_chat,
        button.pay,
        button.web_app,
        button.login_url,
        button.switch_inline_query_chosen_chat,
        button.copy_text,
        button.callback_game
    ]
    
    # This should fail validation but doesn't
    assert all(field is None for field in action_fields)


@given(
    question=text_strategy,
    option_texts=st.lists(text_strategy, min_size=0, max_size=10),
    voter_counts=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10)
)
def test_poll_accepts_invalid_configurations(question, option_texts, voter_counts):
    """Test Poll accepts empty options and negative voter counts."""
    # Make options list match the shorter of the two lists
    min_len = min(len(option_texts), len(voter_counts))
    option_texts = option_texts[:min_len]
    voter_counts = voter_counts[:min_len]
    
    options = [
        types.PollOption(text=text, voter_count=count)
        for text, count in zip(option_texts, voter_counts)
    ]
    
    # Poll accepts empty options list (should require at least 2 options per API)
    poll = types.Poll(
        id="test_poll",
        question=question,
        options=options,
        total_voter_count=sum(voter_counts) if voter_counts else 0,
        is_closed=False,
        is_anonymous=True,
        type="regular",
        allows_multiple_answers=False
    )
    
    assert poll.options == options
    
    # Poll accepts negative voter counts in options
    if any(count < 0 for count in voter_counts):
        assert any(opt.voter_count < 0 for opt in poll.options)


@given(
    total_voter_count=st.integers(min_value=0, max_value=1000),
    option_counts=st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=2,
        max_size=10
    )
)
def test_poll_voter_count_inconsistency(total_voter_count, option_counts):
    """Test that Poll accepts inconsistent voter counts."""
    options = [
        types.PollOption(text=f"Option {i}", voter_count=count)
        for i, count in enumerate(option_counts)
    ]
    
    # Create poll with potentially inconsistent counts
    poll = types.Poll(
        id="test_poll",
        question="Test question?",
        options=options,
        total_voter_count=total_voter_count,
        is_closed=False,
        is_anonymous=True,
        type="regular",
        allows_multiple_answers=False
    )
    
    sum_votes = sum(opt.voter_count for opt in poll.options)
    
    # For single-answer polls, total should equal sum
    # But Poll accepts any total_voter_count
    assert poll.total_voter_count == total_voter_count
    
    # This inconsistency is accepted without validation
    if not poll.allows_multiple_answers and total_voter_count != sum_votes:
        # This should be a validation error but isn't
        assert poll.total_voter_count != sum_votes


@given(
    rows=st.integers(min_value=0, max_value=200),
    cols=st.integers(min_value=0, max_value=20)
)
def test_inline_keyboard_markup_accepts_empty_structures(rows, cols):
    """Test that InlineKeyboardMarkup accepts empty keyboards and rows."""
    # Create keyboard with potentially empty structure
    if rows == 0:
        keyboard = []
    else:
        keyboard = []
        for _ in range(rows):
            if cols == 0:
                keyboard.append([])
            else:
                row = []
                for j in range(cols):
                    btn = types.InlineKeyboardButton(
                        text=f"btn_{j}",
                        callback_data=f"data_{j}"
                    )
                    row.append(btn)
                keyboard.append(row)
    
    # InlineKeyboardMarkup accepts empty keyboards and empty rows
    markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    assert markup.inline_keyboard == keyboard
    
    # Empty keyboards and rows survive serialization
    dumped = markup.model_dump()
    reconstructed = types.InlineKeyboardMarkup(**dumped)
    assert markup == reconstructed


@given(
    duration=st.integers(min_value=-1000, max_value=1000),
    width=st.integers(min_value=-1000, max_value=1000),
    height=st.integers(min_value=-1000, max_value=1000)
)
def test_media_types_accept_negative_values(duration, width, height):
    """Test that media types (Video, Animation) accept negative values."""
    # Test Video
    video = types.Video(
        file_id="video_id",
        file_unique_id="unique_id",
        width=width,
        height=height,
        duration=duration
    )
    
    assert video.width == width
    assert video.height == height
    assert video.duration == duration
    
    # Test Animation
    animation = types.Animation(
        file_id="anim_id",
        file_unique_id="unique_id",
        width=width,
        height=height,
        duration=duration
    )
    
    assert animation.width == width
    assert animation.height == height
    assert animation.duration == duration


# Additional targeted test for specific edge case
def test_inline_keyboard_button_multiple_actions():
    """Test that InlineKeyboardButton accepts multiple action fields simultaneously.
    
    According to API: 'Exactly one of the optional fields must be used'
    """
    # Create button with multiple actions (should be invalid)
    button = types.InlineKeyboardButton(
        text="Multi-action button",
        url="https://example.com",
        callback_data="callback",
        pay=True
    )
    
    # Count non-None action fields
    action_count = sum([
        button.url is not None,
        button.callback_data is not None,
        button.pay is not None
    ])
    
    # This should fail validation (only one action allowed) but doesn't
    assert action_count == 3
    
    # It even serializes fine
    dumped = button.model_dump(exclude_none=True)
    assert 'url' in dumped
    assert 'callback_data' in dumped
    assert 'pay' in dumped