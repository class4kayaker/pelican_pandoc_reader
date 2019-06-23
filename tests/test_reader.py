import pytest
import pelican_pandoc_reader

# Type checking imports
try:
    from typing import Dict
except ImportError:
    pass


def test_standard_attributes():
    assert pelican_pandoc_reader.PandocReader.enabled is True
    assert pelican_pandoc_reader.PandocReader.output_format == "html5"


def test_default_extensions():
    default_extensions = ['md', 'pdc']
    default_formats = {
        'md': 'markdown_mmd',  # Multi-Markdown
        'pdc': 'markdown'  # Pandoc Markdown
    }
    PandocReader = pelican_pandoc_reader.PandocReader
    assert (set(PandocReader.file_extensions) ==
            set(default_extensions))
    assert (set(PandocReader.pandoc_fmt_map.keys()) ==
            set(default_extensions))
    assert all([PandocReader.pandoc_fmt_map[key] == default_formats[key]
                for key in default_extensions])


def test_add_and_reset_extensions():
    fake_fmt_extension = "fake"
    additional_extension = {
        fake_fmt_extension: "fake_format"
    }
    PandocReader = pelican_pandoc_reader.PandocReader
    PandocReader.set_extension_formats(additional_extension)
    assert fake_fmt_extension in PandocReader.file_extensions
    assert fake_fmt_extension in PandocReader.pandoc_fmt_map
    assert (PandocReader.pandoc_fmt_map[fake_fmt_extension] ==
            additional_extension[fake_fmt_extension])
    PandocReader.set_default_formats()
    test_default_extensions()


def test_remove_and_reset_extensions():
    removed_fmt_extension = "md"
    additional_extension_settings = {
        removed_fmt_extension: None
    }
    PandocReader = pelican_pandoc_reader.PandocReader
    PandocReader.set_extension_formats(additional_extension_settings)
    assert removed_fmt_extension not in PandocReader.file_extensions
    assert removed_fmt_extension not in PandocReader.pandoc_fmt_map
    PandocReader.set_default_formats()
    test_default_extensions()


@pytest.fixture
def standard_pandoc_reader():
    mock_settings = {}  # type: Dict[str, str]
    return pelican_pandoc_reader.PandocReader(mock_settings)


@pytest.mark.parametrize("test_settings,test_filename,test_format", [
    ({}, "test_file.pdc", "markdown"),
])
def test_read_fn(standard_pandoc_reader, mocker,
                 test_settings, test_filename, test_format):
    mock_content = "TESTING CONTENT 123"
    mock_metadata = "{'title': 'Mock data'}"
    mocker.patch("pelican_pandoc_reader.PandocReader.read_content",
                 return_value=mock_content)
    mocker.patch("pelican_pandoc_reader.PandocReader.read_metadata",
                 return_value=mock_metadata)
    standard_pandoc_reader.set_extension_formats(test_settings)
    content, metadata = standard_pandoc_reader.read(test_filename)
    standard_pandoc_reader.set_default_formats()
    standard_pandoc_reader.read_content.assert_called_once_with(
        test_filename, fmt=test_format)
    standard_pandoc_reader.read_metadata.assert_called_once_with(
        test_filename, fmt=test_format)
    assert content == mock_content
    assert metadata == mock_metadata
