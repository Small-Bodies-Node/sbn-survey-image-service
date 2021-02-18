# SBN Survey Image Service (Working Draft) v0.1.0-dev

## Deployed Openapi Interface

Live at the PDS [Small Bodies Node](https://)

## What's This?

This repo houses scripts and code to build REST API services that enable a user to retrieve SBN archive images and cutouts thereof. For example, a user may request a full-frame image from the ATLAS survey archive, or a small cutout around their object of interest.  The returned data may be in FITS, JPEG, or PNG formats.  The service can also return the image's PDS label.

The intent is to be compatible with the IVOA's [Simple Image Access protocol](https://www.ivoa.net/documents/SIA/), which is based on the [ObsCore Data Model](https://www.ivoa.net/documents/ObsCore/20111028/).  However, this compatibility is presently incomplete.

## Code Features

- Developed with Postgresql and Sqlite3
- Uses [fitscut](https://github.com/spacetelescope/fitscut) for image cutouts and JPEG/PNG generation
- Flask API layer
- Connexion used to generate swagger interface
- Gunicorn/Apache used for production deployment

## Development Milestones

(DRAFT)

- [x] v0.1, add id, collection, facility, instrument, data product type, calibration level, target, and file paths to database; implement image service for full-frame and sub-frame images, data labels, and conversion to jpeg and png formats.
- [ ] v0.2, search ID, COLLECTION, FACILITY, INSTRUMENT, DPTYPE, FORMAT, MAXREC
- [ ] v0.2, add spatial and time coordinates (including exposure time) to database; implement spatial index; search POS, TIME, EXPTIME
- [ ] v0.3, add spatial resolution and field-of-view to database; search by spatial resolution (SPATRES), field-of-view (FOV)
- [ ] v0.4, add spectral properties to database ("energy" range and spectral resolving power); search by band (BAND), spectral resolving power (SPECRP)
- [ ] v0.5, add polarization, and temporal resolution; search by polarization state (POL), and temporal resolution (TIMERES); allow and ignore UPLOAD
- [ ] v0.6, implement VOSI-availability and VOSI-capabilities resources (/availability and /capabilities)

## Installation and Operations

This repo has code for:

- Running a flask-connexion API
- Testing

The following steps are needed to set up the code base:

- The code base is operated using bash scripts that begin with the `_` underscore character
- Prerequisites for local development:
  - Your choice of database backend, e.g., sqlite3, or a running postgresql server with credentials to read/write.
    - Consider using separate credentials for production and database maintenance.
    - A production instance will only need "select" permissions on the `image` table.
  - python (with pip and venv) v3.6+.
- Clone the repo locally:
  ```
      git clone https://github.com/Small-Bodies-Node/sbn-survey-image-service
      cd sbn-survey-image-service
  ```
- Copy the environment variable definition template and edit to suit your needs: `cp .env-template .env`.
- Always begin by `source _initial_setup.sh`. This will:
  - Create/activate a python virtual environment.
  - Install dependencies (e.g., fitscut) to the virtual env, if needed.
  - Make available to your shell the variables `.env`.
- Optionally test your set up:
  - Be aware that the testing suite will use the database parameters specified in the `.env` file.
    - The database user must have write permissions for testing.
  - `bash _tests`
    - If the test dataset does not exist, then this will take a few minutes.
  - When the test data is no longer needed:
    - Delete test data set from database: `python3 -m sbn_survey_image_service.data.test.generate --delete`.
    - Files in `data/test` must be removed manually.
- Add data to the archive (see below).
- Run in development or deployment modes (see below).

### Adding archival data

The `sbn_survey_image_service.data.add` sub-module is used to add image metadata to the database.  It scans PDS3 or PDS4 labels, and saves to the database data product metadata and URLs to the label and image data.  The sub-module may be run as a command-line script `python3 -m sbn_survey_image_service.data.add`.  The script will automatically create the database in case it does not exist.  For example, to search a NEAT survey directory for PDS4 image labels and data, and to form URLs with which the data may be retrieved:
```
python3 -m sbn_survey_image_service.data.add -r \
    /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata
```

Data may be served to the image service via HTTP(S).  In this case, the `add` script must still be run on locally accessible files, but an appropriate URL may be formed using the `--base-url` and `--strip-leading` parameters:
```
python3 -m sbn_survey_image_service.data.add -r \
    /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata \
    --base-url=https://sbnarchive.psi.edu/pds4/surveys \
    --strip-leading=/path/to/
```

For a summary of command-line parameters, use the `--help` option.

Due to survey-to-survey label differences, it is unlikely that the script will work with a previously untested data source.  Edit the appropriate functions in `sbn_survey_image_service/data/add.py`, either `pds3_image` or `pds4_image`.  For example, the NEAT survey PDS4 data set v1.0 does not have pixel scale in the label, so we have hard coded it into the `pds4_image` function.

It is assumed that survey images are FITS-compatible with a World Coordinate System defined for a standard sky reference frame (ICRS).  The cutout service uses the FITS header, not the PDS labels, to define the sub-frame.  This is a limitation from using `fitscut`.

### API documentation
Whether running in development or deployment modes, the Swagger documentation is available at `http://localhost:API_PORT/ui`, where `API_PORT` is defined in your `.env`.

### Development

If you have `nodemon` globally installed, then you can develop your api code and have it automatically update on changes by running `_develop_apis`. Otherwise, just run `python -m sbn_survey_image_service.api.app`.

### Deployment

A script is supplied called `_gunicorn_manager` that takes the arguments `start|stop|status|restart` to launch the app as a background process with the gunicorn WSGI server for production serving. The number of workers is controlled with the env variable `LIVE_GUNICORN_INSTANCES`. If you have trouble getting gunicorn to work, you can run the manager with 0 as the 2nd argument to start it off in non-daemon mode.

It is recommended that you make the gunicorn-powered server accesible to the outside world by proxy-passing requests through an https-enabled web server like apache.

### Logging
Application error and informational logging is sent to the standard error stream (stderr) and the file specified by the `SBNSIS_LOG_FILE` environment variable.

Successful requests will produce two log items: the parameters and the results as JSON-formatted strings.  The items are linked by a randomly generated job ID:
```
INFO 2021-02-17 14:10:16,960: {"job_id": "013f7515aa074ee58ad5929c8391a366", "id": "urn:nasa:pds:gbo.ast.neat.survey:data_tricam:p20021023_obsdata_20021023113833a", "ra": 47.4495603, "dec": 32.9424075, "size": "5arcmin", "format": "fits", "download": true}
INFO 2021-02-17 14:10:18,339: {"job_id": "013f7515aa074ee58ad5929c8391a366", "filename": "/hylonome3/transient/tmpw8s8qj1b.fits", "attachment_filename": "20021023113833a.fit_47.4495632.94241_5arcmin.fits", "mime_type": "image/fits"}
```
OpenAPI errors (e.g., invalid parameter values from the user) are not logged.  Internal code errors will be logged with a code traceback.