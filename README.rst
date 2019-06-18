Pelican Pandoc Reader
=====================

One of a number of plugins designed to use Pandoc as a reader for generating
Pelican pages. A somewhat official plugin exists at
`pandoc_reader <https://github.com/liob/pandoc_reader>`_, but both is not structured as
a package, and does not make use of Pandoc's YAML metadata block directly.
Development on that repository also appears to be somewhat dead, with no recent
commits, and an open pull request based on an older implementation intended to
make use of the YAML metadata block.
Another plugin `pelican_pandoc <https://github.com/kdheepak/pelican_pandoc>`_
does allow the direct use of Pandoc's YAML metadata, but is somewhat obviously
intended for personal use as it includes more internal customization, and is
also not structured as a package.

This plugin makes use of Pandoc's own option for including a YAML metadata block, which can be exported in JSON format.
In order to make use of this, a template must be provided as a named file readable by Pandoc.
This is done by creating a temporary file with the necessary contents, then removing said file at program termination.

Options
-------

PANDOC_FORMAT_MAP
   Mapping of file extensions to Pandoc names for desired formats
   (i.e. ``markdown+footnotes`` for native markdown with footnotes extension)

PANDOC_ARGS
    Extra command line arguments to be supplied to Pandoc

PANDOC_EXTENSIONS
    Extra filters to be used with Pandoc (command line programs as supplied to ``--filter``)
