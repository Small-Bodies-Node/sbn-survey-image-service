# SBN Survey Image Service (Working Draft) v0.1.0-dev

## Deployed Openapi Interface

Live at the PDS [Small Bodies Node](https://)

## What's This?

This repo houses scripts and code to build REST API services that enable a user to retrieve SBN archive images and cutouts thereof. For example, a user may request a full-frame image from the ATLAS survey archive, or a small cutout around their object of interest.

The intent is to be compatible with the IVOA's [Simple Image Access protocol](https://www.ivoa.net/documents/SIA/).  However, this compatibility is incomplete.

## Code Features

- Developed with Postgresql and Sqlite3
- Uses [fitscut](https://github.com/spacetelescope/fitscut) for image cutouts and JPEG/PNG generation
- Flask API layer
- Connexion used to generate swagger interface
- Gunicorn/Apache used for production deployment

## Development

### Milestones

(DRAFT)

- [x] v0.1, add id, collection, facility, instrument, data product type, calibration level, target, and file paths to database; implement image service for full-frame and sub-frame images, data labels, and conversion to jpeg and png formats.
- [ ] v0.2, search ID, COLLECTION, FACILITY, INSTRUMENT, DPTYPE, FORMAT, MAXREC
- [ ] v0.2, add spatial and time coordinates (including exposure time) to database; implement spatial index; search POS, TIME, EXPTIME
- [ ] v0.3, add spatial resolution and field-of-view to database; search by spatial resolution (SPATRES), field-of-view (FOV)
- [ ] v0.4, add spectral properties to database ("energy" range and spectral resolving power); search by band (BAND), spectral resolving power (SPECRP)
- [ ] v0.5, add polarization, and temporal resolution; search by polarization state (POL), and temporal resolution (TIMERES); allow and ignore UPLOAD
- [ ] v0.6, implement VOSI-availability and VOSI-capabilities resources (/availability and /capabilities)

### Common Steps

This repo has code for:

- Running a flask-connexion API
- Testing

The following steps are needed to set up the code base for whatever aspect you want to work on:

- The codebase is operated using bash scripts that begin with the `\_` underscore character
- Prerequisites for local development:
  - Running postgresql server with credentials to read/write
  - python (& pip) v3.6+
- Clone the repo locally:
  ```
      git clone https://github.com/Small-Bodies-Node/sbn-survey-image-service
      cd sbn-survey-image-service
  ```
- Run `cp .env-template .env` and edit the variables therein
- Always begin by `source _initial_setup.sh`. This will:
  - Create/activate a python virtual environment
  - Install dependencies to virtual env
  - Make available to your shell the variables `.env`
- Optionally test your set up:
  - `bash _tests`.  If the test dataset does not exist, then this will take a few minutes.
  - When the test data is no longer needed:
    - Delete test data set from database: `python3 -m sbn_survey_image_service.data.test.generate --delete`
    - Files in `data/test` must be removed manually.
- Create the database and add data to the archive (see below).

### Adding archival data

The `sbn_survey_image_service.data.add` sub-module is used to add images to the database.  It scans PDS3 or PDS4 labels, and saves data product metadata, path to the label, and path to the image data to the database, indexed by the product ID (PDS3) or logical identifier (PDS4).  The sub-module may be run as a command-line script `python3 -m sbn_survey_image_service.data.add`.  The script will automatically create the database in case it does not exist.  For example, to search a NEAT survey directory for PDS3 image labels and data:
```
python3 -m sbn_survey_image_service.data.add /path/to/archives/neat/tricam/data/p20020718/obsdata
```
For a summary of command-line parameters, use the `--help` option.

Due to survey-to-survey label differences, it is unlikely that the script will work with a previously untested data source.  Edit the appropriate functions in `sbn_survey_image_service/data/add.py`, either `pds3_image` or `pds4_image`.  Also, review the pixel scale calculations in `sbn_survey_image_service/services/image.py` and verify that the correct value will be calculated.

It is assumed that survey images are FITS-compatible with a World Coordinate System defined for a standard sky reference frame (e.g., J2000).  The cutout service uses the FITS header, not the PDS labels, to define the sub-frame.  However, the PDS label is examined for the pixel scale.

### APIs

If you have nodemon globally installed, then you can develop your api code and have it automatically update on changes by running `_develop_apis`. Otherwise, just run `python -m sbn_survey_image_service.api.app`.

## Deployment

A script is supplied called `_gunicorn_manager` that takes the arguments `start|stop|status|restart` to launch the app as a background process with the gunicorn WSGI server for production serving. The number of workers is controlled with the env variable `LIVE_GUNICORN_INSTANCES`. If you have trouble getting gunicorn to work, you can run the manager with 0 as the 2nd argument to start it off in non-daemon mode.

It is recommended that you make the gunicorn-powered server accesible to the outside world by proxy-passing requests through an https-enabled web server like apache.
