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
    mock_set = mocker.patch(
        "pelican_pandoc_reader.PandocReader.set_extension_formats")
    PandocReader.process_settings(test_settings)
    assert PandocReader.extra_args == test_args
    assert PandocReader.filters == test_extensions
    mock_set.assert_called_once_with(
        test_fmt_map)


@pytest.mark.parametrize("test_name", [
    "/fake/root/test_temp_path.template",
    "/fake/root/test_temp_path2.template",
])
def test_metadata_template(mocker, test_name):
    PandocReader = pelican_pandoc_reader.PandocReader

    tmp_file_fn = mocker.patch("tempfile.NamedTemporaryFile",
                               new_callable=mocker.mock_open)
    tmp_file_fn().name = test_name
    tmp_file_fn.reset_mock()
    mock_connect = mocker.patch("pelican.signals.finalized.connect")
    mock_remove = mocker.patch("os.remove")

    assert PandocReader.METADATA_TEMPLATE is None
    PandocReader.create_metadata_template()
    assert PandocReader.METADATA_TEMPLATE == test_name
    tmp_file_fn.assert_called_once_with(
        mode="w", suffix=".template", delete=False)
    tmp_file_fn().write.assert_called_once_with("""$meta-json$""")
    mock_connect.assert_called_once_with(PandocReader.delete_metadata_template)
    PandocReader.delete_metadata_template(None)
    mock_remove.assert_called_once_with(test_name)
    assert PandocReader.METADATA_TEMPLATE is None


@pytest.fixture(params=[
    {},
    {"PANDOC_ARGS": ["--test"]},
    {"PANDOC_EXTENSIONS": ["--test"]},
    {"PANDOC_FORMAT_MAP": {"test": "test_fmt"}},
])
def standard_pandoc_reader(mocker, request):
    test_settings = request.param

    tmp_file_fn = mocker.patch("tempfile.NamedTemporaryFile",
                               new_callable=mocker.mock_open)
    tmp_file_fn().name = "/fake/tmp/path.template"
    tmp_file_fn.reset_mock()
    mocker.patch("pelican.signals.finalized.connect")
    mocker.patch("os.remove")

    pelican_pandoc_reader.PandocReader.process_settings(test_settings)
    yield pelican_pandoc_reader.PandocReader(test_settings)


@pytest.mark.parametrize("test_settings,test_filename,test_format", [
    ({}, "test_file.pdc", "markdown"),
    ({}, "test_file.md", "markdown_mmd"),
    ({"pdc": "markdown+footnotes"}, "test_file.pdc", "markdown+footnotes"),
    ({"fake": "markdown+footnotes"}, "test_file.fake", "markdown+footnotes"),
])
def test_read_fn(standard_pandoc_reader, mocker,
                 test_settings, test_filename, test_format):
    mock_content = "TESTING CONTENT 123"
    mock_metadata = {'title': 'Mock data'}
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


@pytest.mark.parametrize("test_data,test_output", [
    ("", ""),
    ('"%7Bstatic%7Dpath"', '"{static}path"'),
])
def test_read_content(mocker, standard_pandoc_reader, test_data, test_output):
    test_fpath = "/fake/test/path.pdc"
    test_fmt = "fake_fmt"
    mock_pel_open = mocker.patch("pelican.utils.pelican_open",
                                 new_callable=mocker.mock_open,
                                 read_data=test_data)
    mock_pypandoc_convert = mocker.patch("pypandoc.convert_text",
                                         return_value=test_data)

    content = standard_pandoc_reader.read_content(test_fpath, fmt=test_fmt)
    mock_pel_open.assert_called_once_with(test_fpath)
    mock_pypandoc_convert.assert_called_once_with(
        mock_pel_open(), to=standard_pandoc_reader.output_format,
        format=test_fmt,
        extra_args=standard_pandoc_reader.extra_args,
        filters=standard_pandoc_reader.filters)
    assert content == test_output


@pytest.mark.parametrize("test_data,test_output", [
    ('{}', {}),
    ('{"title": "Title"}', {"title": "Title"}),
    ('{"Title": "Title"}', {"title": "Title"}),
])
def test_read_metadata(mocker, standard_pandoc_reader, test_data, test_output):
    test_fpath = "/fake/test/path.pdc"
    test_fmt = "fake_fmt"
    mock_pypandoc_convert = mocker.patch("pypandoc.convert_file",
                                         return_value=test_data)

    content = standard_pandoc_reader.read_metadata(test_fpath, fmt=test_fmt)
    mock_pypandoc_convert.assert_called_once_with(
        test_fpath, to=standard_pandoc_reader.output_format,
        format=test_fmt,
        extra_args=['--template', standard_pandoc_reader.METADATA_TEMPLATE])
    assert content == test_output
