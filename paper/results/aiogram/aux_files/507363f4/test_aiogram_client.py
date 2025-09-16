"""Property-based tests for aiogram.client module using Hypothesis."""

import sys
from pathlib import Path

# Add the aiogram path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/aiogram_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings
from aiogram.client.telegram import SimpleFilesPathWrapper, TelegramAPIServer, BareFilesPathWrapper
from aiogram.client.default import DefaultBotProperties


# Strategy for valid paths (avoiding problematic edge cases)
@st.composite
def valid_paths(draw):
    """Generate valid path strings that can be used with Path objects."""
    segments = draw(st.lists(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="/\\:\0"),
            min_size=1,
            max_size=20
        ),
        min_size=1,
        max_size=5
    ))
    return "/".join(segments)


@st.composite
def path_pairs(draw):
    """Generate pairs of paths that share a common structure."""
    base_segments = draw(st.lists(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="/\\:\0"),
            min_size=1,
            max_size=10
        ),
        min_size=1,
        max_size=3
    ))
    
    server_prefix = draw(st.lists(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="/\\:\0"),
            min_size=1,
            max_size=10
        ),
        min_size=1,
        max_size=2
    ))
    
    local_prefix = draw(st.lists(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="/\\:\0"),
            min_size=1,
            max_size=10
        ),
        min_size=1,
        max_size=2
    ))
    
    server_path = "/" + "/".join(server_prefix)
    local_path = "/" + "/".join(local_prefix)
    test_path = server_path + "/" + "/".join(base_segments)
    
    return server_path, local_path, test_path


class TestSimpleFilesPathWrapper:
    """Test properties of SimpleFilesPathWrapper."""
    
    @given(path_pairs())
    @settings(max_examples=100)
    def test_round_trip_property(self, paths):
        """Test that converting a path from server to local and back gives the original."""
        server_path_str, local_path_str, test_path_str = paths
        
        try:
            server_path = Path(server_path_str)
            local_path = Path(local_path_str)
            test_path = Path(test_path_str)
            
            # Create wrapper
            wrapper = SimpleFilesPathWrapper(server_path, local_path)
            
            # Test round-trip: server -> local -> server
            local_result = wrapper.to_local(test_path)
            back_to_server = wrapper.to_server(local_result)
            
            # The path should be the same after round-trip
            assert Path(back_to_server) == test_path
            
        except ValueError:
            # Skip if path operations fail (e.g., relative_to fails)
            assume(False)


class TestBareFilesPathWrapper:
    """Test properties of BareFilesPathWrapper."""
    
    @given(valid_paths())
    def test_identity_property(self, path_str):
        """Test that BareFilesPathWrapper returns paths unchanged."""
        wrapper = BareFilesPathWrapper()
        path = Path(path_str)
        
        # Both to_local and to_server should return the same path
        assert wrapper.to_local(path) == path
        assert wrapper.to_server(path) == path
        assert wrapper.to_local(path_str) == path_str
        assert wrapper.to_server(path_str) == path_str


class TestTelegramAPIServer:
    """Test properties of TelegramAPIServer."""
    
    @given(
        token=st.text(min_size=1, max_size=100),
        method=st.text(min_size=1, max_size=50)
    )
    def test_api_url_generation(self, token, method):
        """Test that API URL generation correctly substitutes token and method."""
        server = TelegramAPIServer(
            base="https://api.example.com/bot{token}/{method}",
            file="https://api.example.com/file/bot{token}/{path}"
        )
        
        url = server.api_url(token, method)
        
        # URL should contain the token and method
        assert token in url
        assert method in url
        assert url == f"https://api.example.com/bot{token}/{method}"
    
    @given(
        base_url=st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\n\r\t"),
            min_size=10,
            max_size=100
        ).filter(lambda x: not x.endswith("/"))
    )
    def test_from_base_url_generation(self, base_url):
        """Test that from_base correctly generates API server configuration."""
        server = TelegramAPIServer.from_base(base_url)
        
        # Check that the base and file URLs are correctly formatted
        assert server.base == f"{base_url}/bot{{token}}/{{method}}"
        assert server.file == f"{base_url}/file/bot{{token}}/{{path}}"
        
        # Test with trailing slash - should be normalized
        server_with_slash = TelegramAPIServer.from_base(base_url + "/")
        assert server_with_slash.base == server.base
        assert server_with_slash.file == server.file
    
    @given(
        token=st.text(min_size=1, max_size=100),
        path=valid_paths()
    )
    def test_file_url_generation(self, token, path):
        """Test that file URL generation correctly substitutes token and path."""
        server = TelegramAPIServer(
            base="https://api.example.com/bot{token}/{method}",
            file="https://api.example.com/file/bot{token}/{path}"
        )
        
        url = server.file_url(token, path)
        
        # URL should contain the token and path
        assert token in url
        assert str(path) in url
        assert url == f"https://api.example.com/file/bot{token}/{path}"


class TestDefaultBotProperties:
    """Test properties of DefaultBotProperties."""
    
    @given(
        is_disabled=st.booleans(),
        prefer_small=st.booleans(),
        prefer_large=st.booleans(),
        show_above=st.booleans()
    )
    def test_link_preview_auto_creation(self, is_disabled, prefer_small, prefer_large, show_above):
        """Test that link_preview is automatically created when individual options are set."""
        props = DefaultBotProperties(
            link_preview_is_disabled=is_disabled,
            link_preview_prefer_small_media=prefer_small,
            link_preview_prefer_large_media=prefer_large,
            link_preview_show_above_text=show_above
        )
        
        # link_preview should be created automatically
        assert props.link_preview is not None
        assert props.link_preview.is_disabled == is_disabled
        assert props.link_preview.prefer_small_media == prefer_small
        assert props.link_preview.prefer_large_media == prefer_large
        assert props.link_preview.show_above_text == show_above
    
    @given(
        parse_mode=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
        disable_notification=st.one_of(st.none(), st.booleans()),
        protect_content=st.one_of(st.none(), st.booleans())
    )
    def test_getitem_access(self, parse_mode, disable_notification, protect_content):
        """Test that __getitem__ correctly accesses properties."""
        props = DefaultBotProperties(
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            protect_content=protect_content
        )
        
        # Test __getitem__ access
        assert props["parse_mode"] == parse_mode
        assert props["disable_notification"] == disable_notification
        assert props["protect_content"] == protect_content
        
        # Non-existent keys should return None
        assert props["non_existent_key"] is None
    
    def test_no_link_preview_options_no_creation(self):
        """Test that link_preview is not created when no individual options are set."""
        props = DefaultBotProperties(
            parse_mode="HTML",
            disable_notification=True
        )
        
        # link_preview should remain None when no link preview options are set
        assert props.link_preview is None