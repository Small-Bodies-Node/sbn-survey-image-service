"use strict";

import ExifReader from "exifreader";
import { access, writeFile } from "node:fs/promises";

// needed for node
// https://github.com/mattiasw/ExifReader?tab=readme-ov-file#parsing-xmp-tags-when-not-in-a-dom-environment
import { DOMParser, onErrorStopParsing } from "@xmldom/xmldom";

import {
  angular_separation,
  position_angle,
  world_to_pixel,
  getWCSfromXMP,
} from "./avm.js";
import { constants } from "node:buffer";

const DEBUG = false;
const STOP_ON_ERROR = true;
const api = "https://sbnsurveys.astro.umd.edu/api";
// const api = "http://localhost:5014";

// SBN SIS API parameters for image data
const unaligned = {
  id: "urn:nasa:pds:gbo.ast.neat.survey:data_tricam:p20020222_obsdata_20020222120052c",
  format: "jpeg",
  ra: 174.62244,
  dec: 17.97594,
  size: "5arcmin",
  align: false,
  file: "unaligned.jpeg",
};

const aligned = {
  ...unaligned,
  format: "png",
  align: true,
  file: "aligned.png",
};

const atlas = {
  id: "urn:nasa:pds:gbo.ast.atlas.survey.242:58719:02a58719o0648o.fits",
  format: "jpeg",
  ra: 83.63333333333333,
  dec: 22.013333333333332,
  size: "5arcmin",
  align: false,
  file: "atlas.jpeg",
};

/**
 * Fetch an image from the SBN SIS API.
 */
async function fetchImage({ file, id, format, ra, dec, size, align }) {
  return access(file, constants.F_OK)
    .catch((err) => {
      const params = new URLSearchParams({
        format,
        ra,
        dec,
        size,
        align,
      });
      const url = `${api}/images/${id}?` + params.toString();
      console.log(url);
      return fetch(url).then((response) => writeFile(file, response.body));
    })
    .then(() => console.log(`${file} \x1b[32m✓\x1b[0m`));
}

/** Debug messages: to log, or not to log? */
const debug = (...msg) => {
  if (DEBUG) console.debug(...msg);
};

/** simple comparison function */
const compare = (label, a, b, tol) => {
  const passed = Math.abs(a - b) < tol;
  debug(
    label,
    "=",
    a.toFixed(6),
    (a - b).toFixed(6),
    passed ? "\x1b[32mpassed\x1b[0m" : "\x1b[31mfailed\x1b[0m"
  );
  return passed;
};

/**
 * Test separation and position angle from WCS reference value, and WCS
 * transformed pixel position.
 *
 * @param rho0 expected separation [degrees]
 * @param phi0 expected position angle [radians]
 */
function test(label, wcs, ra, dec, rho0, phi0, x0, y0) {

  process.stdout.write("\x1b[35mTesting " + label + "\x1b[0m ");

  // angular separation in degrees
  const rho =
    (angular_separation(wcs.referenceValue[0], wcs.referenceValue[1], ra, dec) *
      180) /
    Math.PI;
  let passed = compare("\nseparation", rho, rho0, 1 / 3600);

  // position angle (phi) of coordinates with respect to the reference value [radians]
  // only test if angular separation is > 0.1 arcsec
  if (rho > 0.1 / 3600) {
    const phi = position_angle(
      wcs.referenceValue[0],
      wcs.referenceValue[1],
      ra,
      dec
    );
    passed *= compare("position angle", phi, phi0, 2 / 206265);
  } else {
    debug("position angle \x1b[34mskipped\x1b[0m");
  }

  const [x, y] = world_to_pixel(wcs, ra, dec);
  passed *= compare("x", x, x0, 0.05);
  passed *= compare("y", y, y0, 0.05);

  console.log(
    "...",
    passed ? "\x1b[32mpassed\x1b[0m" : "\x1b[31mfailed\x1b[0m"
  );

  if (!passed && STOP_ON_ERROR) throw "failure";
}

/**
 * ATLAS specific tests.
 */
function test_atlas(wcs)
{
  process.stdout.write("\x1b[35mTesting ATLAS\x1b[0m ");
  // expected value computed from astropy
  let passed = compare("\nx pixel scale", wcs.scale[0], -0.0005173, 0.0000001);
  passed *= compare("y pixel scale", wcs.scale[1], 0.0005173, 0.0000001);
  // expected value from mskpy.util.getrot
  passed *= compare("rotation", wcs.rotation, -179.83 * Math.PI / 180, 0.001);
  console.log(
    "...",
    passed ? "\x1b[32mpassed\x1b[0m" : "\x1b[31mfailed\x1b[0m"
  );

  if (!passed && STOP_ON_ERROR) throw "failure";
}

console.log("\n\x1b[36m===== js-xmp-example tests =====\x1b[0m");

console.log("\n\x1b[36m----- Fetch files -----\x1b[0m");
await fetchImage({ ...unaligned });
await fetchImage({ ...aligned });
await fetchImage({ ...atlas });

// Get WCS from the unaligned file
console.log("\n\x1b[36m----- Unaligned WCS -----\x1b[0m");
let xmp = await ExifReader.load(unaligned.file, {
  domparser: new DOMParser({ onError: onErrorStopParsing }),
});

if (DEBUG) console.log(xmp);

// unaligned WCS
const uWCS = getWCSfromXMP(xmp);

// test WCS reference values
const ra0 = 174.6223379922916479;
const dec0 = 17.9759266940022933;
test("WCS reference values", uWCS, ra0, dec0, 0, 0, 149, 149);

// test +/-1 pixel
const offset = 1.01 / 3600;
const cdec1 = Math.cos((dec0 * Math.PI) / 180);
let dra1 = offset / cdec1;
test("+1 pixel RA", uWCS, ra0 + dra1, dec0, offset, Math.PI / 2, 148, 149);
test("-1 pixel RA", uWCS, ra0 - dra1, dec0, offset, -Math.PI / 2, 150, 149);
test("+1 pixel Dec", uWCS, ra0, dec0 + offset, offset, 0, 149, 150);
test("-1 pixel Dec", uWCS, ra0, dec0 - offset, offset, Math.PI, 149, 148);

// image origin
const d1 = Math.hypot(148, 148) * offset;
const pa1 = Math.atan2(148, -148) - 0.000175; // fudge it because atan2 is not accurate enough on the sphere
dra1 = (148 * offset) / cdec1;
let ddec1 = -148 * offset;
test("image origin", uWCS, ra0 + dra1, dec0 + ddec1, d1, pa1, 1, 1);

// comet's RA, Dec, separation from WCS center, position angle from WCS center,
// pixel position; expected values computed with astropy
const cometRA = 174.6217388;
const cometDec = 17.9781728;
let sep = 0.00231729;
let pa = 6.03468596 - Math.PI * 2;
test("comet nucleus", uWCS, cometRA, cometDec, sep, pa, 151, 298 - 141);

// Get WCS from the aligned file, which happens to be vertically mirrored with
// respect to unaligned orientation
console.log("\n\x1b[36m----- Aligned WCS -----\x1b[0m");
xmp = await ExifReader.load(aligned.file, {
  domparser: new DOMParser({ onError: onErrorStopParsing }),
});

if (DEBUG) console.log(xmp);

// aligned WCS
const aWCS = getWCSfromXMP(xmp);

test("WCS reference value", aWCS, ra0, dec0, 0.0, 0.0, 149, 298 - 149);

// again, separation and PA calculated with astropy
let label = "hot pixel, FITS position = (152, 176) in DS9";
const pixRA = 174.6214676;
const pixDec = 17.96835083;
sep = 0.00762097;
pa = 3.25044732 - Math.PI * 2;
test(label, aWCS, pixRA, pixDec, sep, pa, 152, 176);

// Test WCS rotation
console.log("\n\x1b[36m----- WCS rotation -----\x1b[0m");
const rotWCS = {
  referenceValue: [10, 0],
  referencePixel: [3, 3],
  scale: [-1, 1], // degrees / pixel
  rotation: 0, // radians
  size: [5, 5],
};

test("0°", rotWCS, 10, 1, 1, 0, 3, 2);

rotWCS.rotation += Math.PI / 4;
test("45°", rotWCS, 10, Math.SQRT2, Math.SQRT2, 0, 2, 2);

rotWCS.rotation += Math.PI / 4;
test("90°", rotWCS, 10, 1, 1, 0, 2, 3);

rotWCS.rotation += Math.PI / 4;
test("135°", rotWCS, 10, Math.SQRT2, Math.SQRT2, 0, 2, 4);

rotWCS.rotation += Math.PI / 4;
test("180°", rotWCS, 10, 1, 1, 0, 3, 4);

rotWCS.rotation += Math.PI / 4;
test("225°", rotWCS, 10, Math.SQRT2, Math.SQRT2, 0, 4, 4);

rotWCS.rotation += Math.PI / 4;
test("270°", rotWCS, 10, 1, 1, 0, 4, 3);

rotWCS.rotation += Math.PI / 4;
test("315°", rotWCS, 10, Math.SQRT2, Math.SQRT2, 0, 4, 2);

// Get WCS from the atlas file, which uses a CD matrix
console.log("\n\x1b[36m----- ATLAS WCS -----\x1b[0m");
xmp = await ExifReader.load(atlas.file, {
  domparser: new DOMParser({ onError: onErrorStopParsing }),
});

if (DEBUG) console.log(xmp);

const atlasWCS = getWCSfromXMP(xmp);
test_atlas(atlasWCS);

console.log();
