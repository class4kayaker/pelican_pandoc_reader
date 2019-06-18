from pelican.readers import BaseReader
from pelican import signals
from pelican.utils import pelican_open

import os
import re
import json
import logging
import tempfile
import atexit

try:
    import pypandoc
except ImportError:
    pypandoc = None

logger = logging.getLogger(__name__)

default_pandoc_fmt_map = {
    'md': 'markdown_mmd',  # Multi-Markdown
    'pdc': 'markdown'  # Pandoc Markdown
}

pelican_url_directive = re.compile(
    r'"\%7B(?P<what>[a-z]+)\%7D(?P<remainder>[^"]*)"'
)


metadata_template_contents = """$meta-json$"""


def un_urlencode(match):
    return '"{'+match.group('what')+'}'+match.group('remainder')+'"'


class PandocReader(BaseReader):
    enabled = bool(pypandoc)
    file_extensions = [key for key in default_pandoc_fmt_map]
    pandoc_fmt_map = default_pandoc_fmt_map
    output_format = 'html5'

    METADATA_TEMPLATE = None

    @staticmethod
    def set_extension_formats(fmt_map):
        for key in fmt_map:
            if fmt_map[key] is None:
                if key in PandocReader.pandoc_fmt_map:
                    del PandocReader.pandoc_fmt_map[key]
            else:
                PandocReader.pandoc_fmt_map[key] = fmt_map[key]
        PandocReader.file_extensions = [
            key for key in PandocReader.pandoc_fmt_map]

    @staticmethod
    def create_metadata_template():
        if PandocReader.METADATA_TEMPLATE is None:
            with tempfile.NamedTemporaryFile(mode="w",
                                             suffix='.template',
                                             delete=False) as f:
                f.write(metadata_template_contents)
                fpath = f.name
            PandocReader.METADATA_TEMPLATE = fpath
            logger.debug("Metadata template file at '%s'", fpath)
            atexit.register(PandocReader.delete_metadata_template)

    @staticmethod
    def delete_metadata_template():
        if PandocReader.METADATA_TEMPLATE is not None:
            logger.debug("Deleting metadata template file at '%s'",
                         PandocReader.METADATA_TEMPLATE)
            fpath = PandocReader.METADATA_TEMPLATE
            PandocReader.METADATA_TEMPLATE = None
            os.remove(fpath)

    def read(self, filename):
        # Get file extension
        _, ext = os.path.splitext(filename)
        fmt = self.pandoc_fmt_map.get(ext[1:]) if ext else None

        self.process_settings(ext)

        # Get meta data
        metadata = self.read_metadata(filename, fmt=fmt)

        # Get content
        content = self.read_content(filename, fmt=fmt)

        return content, metadata

    def process_plugins(self, content):
        return content

    def read_content(self, path, fmt=None):
        with pelican_open(path) as fp:
            content = pypandoc.convert_text(
                fp, to=self.output_format,
                format=fmt,
                extra_args=self.extra_args, filters=self.filters
            )

        return self.process_plugins(
            pelican_url_directive.sub(un_urlencode, content)
        )

    def read_metadata(self, path, fmt=None):
        metadata_json = pypandoc.convert_file(
            path, to=self.output_format,
            format=fmt,
            extra_args=['--template', self.METADATA_TEMPLATE]
        )

        metadata = dict()
        for key, value in json.loads(metadata_json).items():
            # Make key lower case to match processor definitions.
            key = key.lower()
            metadata[key] = self.process_metadata(key, value)

        return metadata

    def process_settings(self, ext):
        self.extra_args = self.settings.get('PANDOC_ARGS', [])
        self.filters = self.settings.get('PANDOC_EXTENSIONS', [])


def add_reader(readers):
    logger.debug("Setting extensions mapping")
    PandocReader.set_extension_formats(
        readers.settings.get("PANDOC_FORMAT_MAP", {}))

    logger.debug("Creating metadata template file")
    PandocReader.create_metadata_template()

    logger.debug("Adding PandocReader to readers")
    for ext in PandocReader.pandoc_fmt_map:
        readers.reader_classes[ext] = PandocReader


def register():
    logger.debug("Registering pelican_pandoc_reader plugin.")
    signals.readers_init.connect(add_reader)
