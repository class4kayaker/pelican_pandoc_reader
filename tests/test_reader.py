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


@pytest.mark.parametrize(
    "test_settings,test_args,"
    "test_extensions,test_fmt_map", [
        ({}, [], [], {}),
        ({"PANDOC_ARGS": ["--test"]}, ["--test"], [], {}),
        ({"PANDOC_EXTENSIONS": ["--test"]}, [], ["--test"], {}),
        ({"PANDOC_FORMAT_MAP": {"test": "test_fmt"}}, [], [],
         {"test": "test_fmt"}),
    ]
)
def test_settings(mocker, test_settings,
                  test_args, test_extensions, test_fmt_map):
    PandocReader = pelican_pandoc_reader.PandocReader
    mocker.patch("pelican_pandoc_reader.PandocReader.set_extension_formats")
    PandocReader.process_settings(test_settings)
    assert PandocReader.extra_args == test_args
    assert PandocReader.filters == test_extensions
    PandocReader.set_extension_formats.assert_called_once_with(
        test_fmt_map)


@pytest.fixture
def standard_pandoc_reader():
    mock_settings = {}  # type: Dict[str, str]
    return pelican_pandoc_reader.PandocReader(mock_settings)


@pytest.mark.parametrize("test_settings,test_filename,test_format", [
    ({}, "test_file.pdc", "markdown"),
    ({}, "test_file.md", "markdown_mmd"),
    ({"pdc": "markdown+footnotes"}, "test_file.pdc", "markdown+footnotes"),
    ({"fake": "markdown+footnotes"}, "test_file.fake", "markdown+footnotes"),
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
