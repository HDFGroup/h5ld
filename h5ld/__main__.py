import sys
import argparse
import h5py
from . import AllotropeDF


cli = argparse.ArgumentParser(
    prog="python -m h5ld",
    description="Dump linked data from HDF5 file in several RDF file formats.",
    epilog="Copyright 2021 The HDF Group <https://www.hdfgroup.org/>",
)
cli.add_argument("h5file", help="HDF5 file with linked data", metavar="H5FILE")
cli.add_argument(
    "--check",
    "-c",
    action="store_true",
    help="Check if HDF5 file has useable linked data content",
)
cli.add_argument(
    "--format",
    "-f",
    metavar="FMT",
    choices=["nquads", "json-ld", "turtle", "trig"],
    default="turtle",
    help='FMT one of: "nquads", "json-ld", "turtle" (default), "trig"',
)
cli.add_argument("--output", "-o", metavar="FILE", help="Save output to FILE")
arg = cli.parse_args()

formats = [AllotropeDF]

with h5py.File(arg.h5file, mode="r") as f:
    # Find a reader class for the input HDF5 file...
    for cls in formats:
        if cls.verify_format(f):
            break
    else:
        raise SystemExit(f'Unsupported data content in "{arg.h5file}".')

    if arg.check:
        if not cls.check_ld(f, report=True):
            print(f'"{arg.h5file}" has unsupported linked data storage format')
            print("Supported linked data formats:")
            for _ in formats:
                print(f"   * {_.name} ({_.short_name})")
    else:
        ld = cls(f)
        ld.dump_ld(destination=(arg.output or sys.stdout.buffer), format=arg.format)
