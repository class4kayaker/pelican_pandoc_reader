from pelican.readers import BaseReader
from pelican import signals
from pelican.utils import pelican_open

import os
import re
import json
import logging
import tempfile
import atexit

import pypandoc

logger = logging.getLogger(__name__)

pandoc_fmt_map = {
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
    enabled = True
    file_extensions = [key for key in pandoc_fmt_map]
    output_format = 'html5'

    METADATA_TEMPLATE = None

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
        # Get meta data
        _, ext = os.path.splitext(filename)
        fmt = pandoc_fmt_map.get(ext[1:]) if ext else None

        metadata = self.read_metadata(filename, format=fmt)

        # Get content
        self.process_settings()

        with pelican_open(filename) as fp:
            content = pypandoc.convert_text(
                fp, to=self.output_format,
                format=fmt,
                extra_args=self.extra_args, filters=self.filters
            )

        content = self.process_plugins(
            pelican_url_directive.sub(un_urlencode, content)
        )

        return content, metadata

    def process_plugins(self, content):
        return content

    def read_metadata(self, path, format=None):
        metadata_json = pypandoc.convert_file(
            path, to=self.output_format,
            format=format,
            extra_args=['--template', self.METADATA_TEMPLATE]
        )

        _metadata = json.loads(metadata_json)
        metadata = dict()
        for key, value in _metadata.items():
            if key == 'author' and isinstance(value, list):
                key = 'authors'
            metadata[key] = self.process_metadata(key, value)
        return metadata

    def process_settings(self):
        self.extra_args = self.settings.get('PANDOC_ARGS', [])
        self.filters = self.settings.get('PANDOC_EXTENSIONS', [])


def add_reader(readers):
    logger.debug("Creating metadata template file")
    PandocReader.create_metadata_template()
    logger.debug("Adding PandocReader to readers")
    for ext in PandocReader.file_extensions:
        readers.reader_classes[ext] = PandocReader


def register():
    logger.debug("Registering pandoc_reader plugin.")
    signals.readers_init.connect(add_reader)
