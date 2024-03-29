# SBN Survey Image Service v0.2.0

## Deployed Openapi Interface

Live at the PDS [Small Bodies Node](https://sbnsurveys.astro.umd.edu/api/ui)

## What's This?

The SBN Survey Image Service is a REST API that enables a user to retrieve archive images and cutouts thereof from the Planetary Data System's Small-Bodies Node (PDS SBN). For example, a user may request a full-frame image from the ATLAS survey archive, or a small cutout around their object of interest. The returned data may be in FITS, JPEG, or PNG formats. The service can also return the image's PDS label.

![SBN Survey Image Service workflow](docs/SBNSIS-workflow.png)

## Code Features

- Uses [fitscut](https://github.com/spacetelescope/fitscut) for image cutouts and JPEG/PNG generation
- Flask API layer
- OpenAPI spec with Connexion and Swagger
- Gunicorn for production deployment
- Backed by Postgresql or Sqlite3

## Development

- [ ] resolve image locations using the PSD registry
- [ ] deploy as an AWS Lambda service?

## Requirements

- [libtool](https://www.gnu.org/software/libtool/)

## Installation and Operations

This repo has code for:

- Running the API
- Testing

Most day-to-day tasks can be accomplished with the `_sbnsis` command.

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

- Initialize your installation with `bash _initial_setup.sh`. This will:
  - Create and activate a python virtual environment.
    - To use a specific Python interpreter, set the PYTHON environment variable: `PYTHON=/path/to/python3 bash _install_setup.sh`
  - Install dependencies, including `fitscut`, to the virtual env.
- Create a new environment variable file and edit to suit your needs: `_sbnsis env`.
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

The `sbn_survey_image_service.data.add` sub-module is used to add image metadata to the database. It scans PDS3 or PDS4 labels, and saves to the database data product metadata and URLs to the label and image data. The sub-module may be run as a command-line script `python3 -m sbn_survey_image_service.data.add`. The script will automatically create the database in case it does not exist. For example, to search a NEAT survey directory for PDS4 image labels and data, and to form URLs with which the data may be retrieved:

```
python3 -m sbn_survey_image_service.data.add -r \
    /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata
```

The previous example is for a survey accessible via the local file system. As an alternative, data may be served to the image service via HTTP(S). In this case, the `add` script must still be run on locally accessible labels, but an appropriate URL may be formed using the `--base-url` and `--strip-leading` parameters:

```
python3 -m sbn_survey_image_service.data.add -r \
    /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata \
    --base-url=https://sbnarchive.psi.edu/pds4/surveys \
    --strip-leading=/path/to/
```

For a summary of command-line parameters, use the `--help` option.

Due to survey-to-survey label differences, it is unlikely that the script will work with a previously untested data source. Edit the appropriate functions in `sbn_survey_image_service/data/add.py`, either `pds3_image` or `pds4_image`. For example, the NEAT survey PDS4 data set v1.0 does not have pixel scale in the label, so we have hard coded it into the `pds4_image` function.

It is assumed that survey images are FITS-compatible with a World Coordinate System defined for a standard sky reference frame (ICRS). The cutout service uses the FITS header, not the PDS labels, to define the sub-frame. This is a limitation from using `fitscut`.

### API documentation

Whether running in development or deployment modes, the Swagger documentation is available at `http://localhost:API_PORT/ui`, where `API_PORT` is defined in your `.env`.

### Development

If you have `nodemon` globally installed, then you can develop your api code and have it automatically update on changes by running `_sbnsis start --dev_`. Otherwise, just run `python -m sbn_survey_image_service.api.app`.

### Deployment

The `_sbnsis` takes the arguments `start|stop|status|restart` to launch the app as a background process with the gunicorn WSGI server for production serving. The number of workers is controlled with the env variable `LIVE_GUNICORN_INSTANCES`. If you have trouble getting gunicorn to work, running in non-daemon mode may help with debugging: `_sbnsis start --no-daemon`.

It is recommended that you make the gunicorn-powered server accesible to the outside world by proxy-passing requests through an https-enabled web server like apache.

### Logging

Application error and informational logging is sent to the standard error stream (stderr) and the file specified by the `SBNSIS_LOG_FILE` environment variable.

Successful requests will produce two log items: the parameters and the results as JSON-formatted strings. The items are linked by a randomly generated job ID:

```
INFO 2021-02-17 14:10:16,960: {"job_id": "013f7515aa074ee58ad5929c8391a366", "id": "urn:nasa:pds:gbo.ast.neat.survey:data_tricam:p20021023_obsdata_20021023113833a", "ra": 47.4495603, "dec": 32.9424075, "size": "5arcmin", "format": "fits", "download": true}
INFO 2021-02-17 14:10:18,339: {"job_id": "013f7515aa074ee58ad5929c8391a366", "filename": "/hylonome3/transient/tmpw8s8qj1b.fits", "download_filename": "20021023113833a.fit_47.4495632.94241_5arcmin.fits", "mime_type": "image/fits"}
```

OpenAPI errors (e.g., invalid parameter values from the user) are not logged. Internal code errors will be logged with a code traceback.
