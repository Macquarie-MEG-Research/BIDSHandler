# A number of extensions that can provide functionality with other analysis
# packages.

import os.path as op
from .constants import MEG_MANUFACTURERS, MEG_MAN1, MEG_MAN2
from .utils import _get_mrk_meas_date, _realize_paths


def mne_params(scan):
    """Generate the parameters required to create a MNE raw instance.

    Parameters
    ----------
    scan : :py:func:`bindshandler.Scan`
        The Scan object to return the parameters of.

    Returns
    -------
    parameters : dict
        Dictionary of parmaeters.

    Examples
    --------
    If we have a `Scan` object already (for example, of a KIT scan), we can
    simply enter:

    .. code:: python

        >>> mne.io.read_raw_kit(**mne_params(scan))

    This will return the appropriate MNE raw object.
    """
    # This is currently only going to be possible for MEG data
    if not scan.scan_type == 'meg':
        raise ValueError("Only MEG supported currently.")
    ext = op.splitext(scan.raw_file)[1]
    manufacturer = MEG_MANUFACTURERS.get(ext, None)

    parameters = dict()

    # Depending on the manufacturer we will need to return different data.
    if manufacturer == MEG_MAN1:
        # KIT/Yokogawa data
        parameters['input_fname'] = scan.raw_file
        marker_vals = list()
        markers = {key: value for key, value in scan.associated_files.items()
                   if 'markers' in key}
        if len(markers) == 2:
            # If the recommended naming is used it is easy
            if 'markers-pre' in markers and 'markers-post' in markers:
                marker_vals = [markers['markers-pre'], markers['markers-post']]
            # otherwise try and get the times from the marker itself.
            else:
                marker_vals = list(markers.values())
                marker_vals.sort(_get_mrk_meas_date)
        elif len(markers) != 0:
            marker_vals = list(markers.values())
        elif len(markers) == 0:
            marker_vals = None
        parameters['mrk'] = _realize_paths(scan, marker_vals)
        if marker_vals is not None:
            headshapes = [value for key, value in scan.associated_files.items()
                          if 'headshape' in key]
            for key in ['hsp', 'elp']:
                for val in headshapes:
                    if key in val:
                        parameters[key] = _realize_paths(scan, val)
    elif manufacturer == MEG_MAN2:
        # Elekta data
        parameters['fname'] = scan.raw_file
    return parameters
