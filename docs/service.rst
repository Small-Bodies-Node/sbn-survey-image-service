Service Deployment
==================

Most day-to-day tasks can be accomplished with the `sbnsis` command.

.. code-block:: text

   $ sbnsis --help
   usage: sbnsis [-h] {start,restart,status,stop,rotate-logs,env} ...

   SBN Survey Image Service

   positional arguments:
   {start,restart,status,stop,rotate-logs,env}
                           sub-command help
      start               start the service
      restart             restart the service
      status              get service status
      stop                stop the service
      rotate-logs         force rotate logs
      env                 create a new .env file

   options:
   -h, --help            show this help message and exit


Production service
------------------

Start the service in production mode:

.. code:: bash

   sbnsis start

The app will launch as a background process with the gunicorn WSGI server. The number of workers is controlled with the env variable ``LIVE_GUNICORN_INSTANCES``. If you have trouble getting gunicorn to work, running in non-daemon mode may help with debugging:

.. code:: bash

    sbnsis start --no-daemon

See :doc:`adding-data` for instructions on how to add data to the database.  The service does not need to be running to add data.

It is recommended that you make the gunicorn-powered server accessible to the outside world by proxy-passing requests through an HTTPS-enabled web server like Apache.


REST API
--------

Whether running in development or deployment modes, the Swagger documentation for the REST API is available at ``http://localhost:API_PORT/BASE_HREF/ui``, where ``API_PORT`` and ``BASE_HREF`` is defined in your ``.env``.


Logging
-------

Application error and informational logging is sent to the standard error stream (stderr) and the file specified by the ``SBNSIS_LOG_FILE`` environment variable.  If this is set to use the `logging/` directory in the repository, then the `sbnsis` tool will be able to automatically rotate logs using `logrotate` and the `logging/logrotate.config` file.  If `SBNSIS_LOG_FILE` is set to another location, the `logrotate.config` file should be edited, or else log rotation will not work.  Successful requests will produce two log items: the parameters and the results as JSON-formatted strings. The items are linked by a randomly generated job ID:

.. code:: text

   INFO 2021-02-17 14:10:16,960: {"job_id": "013f7515aa074ee58ad5929c8391a366", "id": "urn:nasa:pds:gbo.ast.neat.survey:data_tricam:p20021023_obsdata_20021023113833a", "ra": 47.4495603, "dec": 32.9424075, "size": "5arcmin", "format": "fits", "download": true}
   INFO 2021-02-17 14:10:18,339: {"job_id": "013f7515aa074ee58ad5929c8391a366", "filename": "/hylonome3/transient/tmpw8s8qj1b.fits", "download_filename": "20021023113833a.fit_47.4495632.94241_5arcmin.fits", "mime_type": "image/fits"}


OpenAPI errors (e.g., invalid parameter values from the user) are not logged.  Internal code errors will be logged with a code traceback.


User agent
----------

All HTTP requests made by the service will have a user agent of "SBN Survey Image Service {version}".


Updating SBNSIS
---------------

For minor updates that only require a restart of the server, first tag a release on Github with the new version, e.g., v0.3.3.  Then, pull the updated code and the new tag, upgrade the SIS, and restart the service:

.. code:: bash

   git pull
   pip install -U .
   sbnsis restart
