# SBN Survey Image Service

## What is This?

The SBN Survey Image Service is a REST API that enables a user to retrieve archive images and cutouts thereof from the Planetary Data System's Small-Bodies Node (PDS SBN). For example, a user may request a full-frame image from the ATLAS survey archive, or a small cutout around their object of interest. The returned data may be in FITS, JPEG, or PNG formats. The service can also return the image's PDS label.

![SBN Survey Image Service workflow](docs/_static/SBNSIS-workflow.png)

The [SBN Survey Image Service](https://sbnsurveys.astro.umd.edu/api/ui) (SIS) is deployed and available for [PDS Small-Bodies Node](https://pds-smallbodies.astro.umd.edu/) survey holdings. See the [API User’s Guide](https://sbn-survey-image-service.readthedocs.io/en/latest/api-guide.html) or the [API documentation](https://sbnsurveys.astro.umd.edu/api/ui) for details.

## Code Features

- Flask API layer
- OpenAPI spec with Connexion and Swagger
- Gunicorn for production deployment
- Backed by Postgresql or Sqlite3

## Documentation

Documentation is provided in the ``/docs`` directory, and at [readthedocs](https://sbn-survey-image-service.readthedocs.io).
