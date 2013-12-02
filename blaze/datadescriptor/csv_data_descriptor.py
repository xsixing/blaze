from __future__ import absolute_import
import operator
import contextlib
import ctypes
import csv

from .data_descriptor import IDataDescriptor
from .. import datashape
from dynd import nd, ndt
from .dynd_data_descriptor import DyNDDataDescriptor


def csv_descriptor_iter(csvfile, schema, blen=1, start=None, stop=None):
    if blen == 1:
        for row in csv.reader(csvfile):
            yield DyNDDataDescriptor(nd.array(row, dtype=schema))
    else:        
        rows = []
        for nrow, row in enumerate(csv.reader(csvfile)):
            rows.append(row)
            if nrow % blen == 0:
                yield DyNDDataDescriptor(nd.array(rows, dtype=schema))
                rows = []


class CSVDataDescriptor(IDataDescriptor):
    """
    A Blaze data descriptor which exposes a CSV file.

    Parameters
    ----------
    csvfile : file IO handle
        A file handler for teh CSV file.
    schema : string or blaze.datashape
        A blaze datashape (or its string representation) of the schema
        in the CSV file.
    """
    def __init__(self, csvfile, schema):
        if not hasattr(csvfile, "__iter__"):
            raise TypeError('csvfile does not have an iter interface')
        self.csvfile = csvfile
        if type(schema) in (str, unicode):
            schema = datashape.dshape(schema)
        if not isinstance(schema, datashape.Record):
            raise TypeError(
                'schema cannot be converted into a blaze record dshape')
        self.schema = str(schema)

    @property
    def persistent(self):
        return True

    @property
    def is_concrete(self):
        """Returns False, CSV arrays are not concrete."""
        return True

    @property
    def dshape(self):
        return datashape.dshape('Var, %s' % self.schema)

    @property
    def writable(self):
        return False

    @property
    def appendable(self):
        return True

    @property
    def immutable(self):
        return False

    def dynd_arr(self):
        # Positionate at the beginning of the file
        self.csvfile.seek(0)
        return nd.array(csv.reader(self.csvfile), dtype=self.schema)

    def __array__(self):
        return nd.as_numpy(self.dynd_arr())

    def __len__(self):
        # We don't know how many rows we have
        return None

    def __getitem__(self, key):
        # CSV files cannot be accessed randomly
        raise NotImplementedError

    def __setitem__(self, key, value):
        # CSV files cannot be updated (at least, not efficiently)
        raise NotImplementedError

    def __iter__(self):
        # Positionate at the beginning of the file
        self.csvfile.seek(0)
        return csv_descriptor_iter(self.csvfile, self.schema)

    def append(self, values):
        """Append a list of values."""
        return NotImplementedError

    def iterchunks(self, blen=None, start=None, stop=None):
        """Return chunks of size `blen` (in leading dimension).

        Parameters
        ----------
        blen : int
            The length, in rows, of the buffers that are returned.
        start : int
            Where the iterator starts.  The default is to start at the
            beginning.
        stop : int
            Where the iterator stops. The default is to stop at the end.

        Returns
        -------
        out : iterable
            This iterable returns buffers as DyND arrays,

        """
        # Return the iterable
        self.csvfile.seek(0)
        return csv_descriptor_iter(self.csvfile, self.schema,
                                   blen, start, stop)
