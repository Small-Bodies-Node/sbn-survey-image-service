# Using Astronomy Visualization Metadata with Javascript

[avm.js](avm.js) contains code to convert from celestial coordinates (right ascension and declination) to image coordinates using [Astronomy Visualization Metadata](https://www.virtualastronomy.org/avm_metadata.php) saved in an image file (XMP format). In particular, it is designed to work with the [SBN Survey Image Service (SBN SIS)](https://sbn-survey-image-service.readthedocs.io/), which produces JPEG and PNG cutouts of survey data annotated with AVM standardized parameters.

## How to use

The following example will get an ATLAS image cutout from the SBN SIS, read in its XMP tags and extract the world coordinate system information, then convert a coordinate into a the pixel position:

```js
// first get the XMP data from an image
const url =
  "https://sbnsurveys.astro.umd.edu/api/images/" +
  "urn:nasa:pds:gbo.ast.atlas.survey.235:58505:02a58505o0340h.fits" +
  "?ra=83.63333333333333&dec=22.013333333333332&size=5arcmin&format=jpeg";

const xmp = fetch(url)
  .then((response) => response.arrayBuffer())
  .then((image) => ExifReader.load(image));

// get the needed AVM metadata in a "wcs" object
const wcs = getWCSfromXMP(xmp);

// convert RA and Dec to pixel coordinates:
//   * (x, y) = (1, 1) is the upper-left corner on the screen
//   * integer coordinates refer to the center of the pixel
const [x, y] = world_to_pixel(wcs, 83.633333, 22.013333);
```

## Testing

To run the testing suite, install needed modules, and run `test.js` with node:

```bash
npm install
node test.js
```
