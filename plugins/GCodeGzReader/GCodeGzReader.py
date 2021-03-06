# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import gzip

from UM.Mesh.MeshReader import MeshReader #The class we're extending/implementing.
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType #To add the .gcode.gz files to the MIME type database.
from UM.PluginRegistry import PluginRegistry

import contextlib
import resource


@contextlib.contextmanager
def limit(limit, type=resource.RLIMIT_AS):
    soft_limit, hard_limit = resource.getrlimit(type)
    resource.setrlimit(type, (limit, hard_limit)) # set soft limit
    try:
        yield
    finally:
        resource.setrlimit(type, (soft_limit, hard_limit)) # restore


##  A file reader that reads gzipped g-code.
#
#   If you're zipping g-code, you might as well use gzip!
class GCodeGzReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-cura-compressed-gcode-file",
                comment = "Cura Compressed GCode File",
                suffixes = ["gcode.gz"]
            )
        )
        self._supported_extensions = [".gcode.gz"]

    def _read(self, file_name):
        with open(file_name, "rb") as file:
            file_data = file.read()

        with limit(1 << 30):  # Prevent a gzip bomb (by setting the max size to 1 gig)
            uncompressed_gcode = gzip.decompress(file_data).decode("utf-8")
        PluginRegistry.getInstance().getPluginObject("GCodeReader").preReadFromStream(uncompressed_gcode)
        result = PluginRegistry.getInstance().getPluginObject("GCodeReader").readFromStream(uncompressed_gcode, file_name)

        return result
