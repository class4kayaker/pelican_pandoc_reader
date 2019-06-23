import pytest
import pelican_pandoc_reader as pelpr


def test_default_extensions():
    default_extensions = ['md', 'pdc']
    default_formats = {
        'md': 'markdown_mmd',  # Multi-Markdown
        'pdc': 'markdown'  # Pandoc Markdown
    }
    assert (set(pelpr.PandocReader.file_extensions) ==
            set(default_extensions))
    assert (set(pelpr.PandocReader.pandoc_fmt_map.keys()) ==
            set(default_extensions))
    assert all([pelpr.PandocReader.pandoc_fmt_map[key] == default_formats[key]
                for key in default_extensions])


def test_add_and_reset_extensions():
    fake_fmt_extension = "fake"
    additional_extension = {
        fake_fmt_extension: "fake_format"
    }
    pelpr.PandocReader.set_extension_formats(additional_extension)
    assert fake_fmt_extension in pelpr.PandocReader.file_extensions
    assert fake_fmt_extension in pelpr.PandocReader.pandoc_fmt_map
    assert (pelpr.PandocReader.pandoc_fmt_map[fake_fmt_extension] ==
            additional_extension[fake_fmt_extension])
    pelpr.PandocReader.set_default_formats()
    test_default_extensions()


def test_remove_and_reset_extensions():
    removed_fmt_extension = "md"
    additional_extension_settings = {
        removed_fmt_extension: None
    }
    pelpr.PandocReader.set_extension_formats(additional_extension_settings)
    assert removed_fmt_extension not in pelpr.PandocReader.file_extensions
    assert removed_fmt_extension not in pelpr.PandocReader.pandoc_fmt_map
    pelpr.PandocReader.set_default_formats()
    test_default_extensions()


@pytest.fixture
def standard_pandoc_reader():
    mock_settings = {}
    return pelpr.PandocReader(mock_settings)


def test_read_content(standard_pandoc_reader):
    pass
