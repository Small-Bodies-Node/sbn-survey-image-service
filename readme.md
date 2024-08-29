# SBN Survey Image Service

Live at the PDS [Small Bodies Node](https://sbnsurveys.astro.umd.edu/api/ui)

## What is This?

The SBN Survey Image Service is a REST API that enables a user to retrieve archive images and cutouts thereof from the Planetary Data System's Small-Bodies Node (PDS SBN). For example, a user may request a full-frame image from the ATLAS survey archive, or a small cutout around their object of interest. The returned data may be in FITS, JPEG, or PNG formats. The service can also return the image's PDS label.

![SBN Survey Image Service workflow](docs/_static/SBNSIS-workflow.png)

## Code Features

- Uses [fitscut](https://github.com/spacetelescope/fitscut) for image cutouts and JPEG/PNG generation
- Flask API layer
- OpenAPI spec with Connexion and Swagger
- Gunicorn for production deployment
- Backed by Postgresql or Sqlite3

## Documentation

Documentation is provided in the docs directory, and at
![readthedocs](https://sbn-survey-image-service.readthedocs.io).
