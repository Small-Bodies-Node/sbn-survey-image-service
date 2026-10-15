from astropy.wcs import WCS


def north_up_wcs(native: WCS, shape: tuple[int, int]) -> WCS:
    """Canonical equatorial TAN view; shape is (rows, columns), FITS is (x, y).

    Keep the native array and WCS for science. This WCS describes a derived
    display, including rectangular/clipped cutouts and off-image CRPIX values.
    """
    height, width = shape
    result = WCS(naxis=2)
    result.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    result.wcs.crpix = [(width + 1) / 2, (height + 1) / 2]
    center = native.celestial.pixel_to_world((width - 1) / 2, (height - 1) / 2)
    result.wcs.crval = [center.icrs.ra.deg, center.icrs.dec.deg]
    scales = [abs(scale.value) for scale in native.celestial.proj_plane_pixel_scales()]
    result.wcs.cdelt = [-float(scales[0]), float(scales[1])]
    result.wcs.radesys = "ICRS"
    result.pixel_shape = (width, height)
    return result
