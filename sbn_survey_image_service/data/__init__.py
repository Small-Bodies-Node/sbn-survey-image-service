# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Data functions."""

import io


def valid_pds3_label(filename: str) -> bool:
    """Test that this is probably a PDS3 label."""

    inf: io.IOBase
    with open(filename, 'r', newline='\r\n') as inf:
        # read at most 100 lines, looking for PDS_VERSION_ID
        n: int = 0
        line: str = ''
        for line in inf:
            n += 1
            if line.strip() == '':
                continue
            if line.strip().replace(' ', '') == 'PDS_VERSION_ID=PDS3':
                return True
        return False
