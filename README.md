# `h5ld`: HDF5 Linked Data

[Linked Data](https://www.w3.org/standards/semanticweb/data) are becoming more popular for user-created metadata in HDF5 files. This Python package provides readers for the HDF5-based formats with such metadata . Entire linked data content is read in one operation and made available as an [_rdflib_](https://rdflib.readthedocs.io) graph object.

Currently supported:
* [Allotrope Data Format](https://docs.allotrope.org/) (ADF)

## Installation

    pip install git+https://github.com/HDFGroup/h5ld@{LABEL}

where `{LABEL}` is either `master` or a tag label.

Requirements:

* Python >= 3.7
* h5py >= 3.3.0
* rdflib >= 5.0.0

## License

This software is open source. See [this file](./LICENSE) for details.

## Quick Start

This package can be used either as a command-line tool or programmatically. On the command-line, the package dumps the link data of an input HDF5 file into several popular RDF formats supported by the _rdflib_ package. For example:

    python -m h5ld -f json-ld -o output.json INPUT.h5

will dump the input file's RDF data to a file `output.json` in the JSON-LD format. Omitting an output file prints out the same content so it can be ingested by another command-line tool. Full description is available from:

    python -m h5ld --help

There is also a programmatic interface for integration into Python applications. Each h5ld reader will provide the following methods and attributes:

* File format name.

    ```python
    print(f"Input file format is: {reader.name}")
    ```

* Short (usually an acronym) of the file format.

    ```python
    print(f"File format acronym: {reader.short_name}")
    ```

* Check if the reader is the right choice for the input file.

    ```python
    with h5py.File("input.h5", mode="r") as f:
        if reader.verify_format(f):
            # Do something...
          else:
              print("Sorry but not the right h5ld reader.")
    ```

* Check if there is linked data content in the input HDF5 file. Optionally, print an appropriate description of the data.

    ```python
    with h5py.File("input.h5", mode="r") as f:
        reader.check_ld(f, report=True)
    ```

* Read linked data and export it to a `destination` in the requested RDF `format`.

    ```python
    with h5py.File("input.h5", mode="r") as f:
        reader(f).dump_ld("output.json", format="json-ld")
    ```

* Read linked data and return either an `rdflib.Graph` or `rdflib.ConjunctiveGraph` object.

    ```python
    with h5py.File("input.h5", mode="r") as f:
        graph = reader(f).get_ld()
    ```

* A Python dictionary with the reader's namespace prefixes and their IRIs.

    ```python
    with h5py.File("input.h5", mode="r") as f:
        rdr = reader(f)
        namespaces = rdr.namespaces
    ```
