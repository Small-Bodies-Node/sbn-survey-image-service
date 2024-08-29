.. SBN Survey Image Service documentation master file, created by
   sphinx-quickstart on Thu Aug 29 09:53:40 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SBN Survey Image Service
========================

The SBN Survey Image Service (SIS) is a REST API that enables a user to retrieve
archive images and cutouts thereof from the Planetary Data System's Small-Bodies
Node (PDS SBN). The returned data may be in FITS, JPEG, or PNG formats. The
service can also return the image's PDS label.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. image:: _static/SBNSIS-workflow.png

Installation and setup
----------------------

Select and install your choice of database backend, either sqlite3 or
postgresql.  If using postgresql, it is recommended to have two separate users
with access: one that can perform database maintenance (e.g., INSERT and UPDATE
permissions), and another that will be limited to read-only access.


SBN SIS
^^^^^^^

Checkout the code:

.. code:: bash

   git clone https://github.com/Small-Bodies-Node/sbn-survey-image-service
   cd sbn-survey-image-service

For the production service, generally checkout a specific release, e.g., v0.3.3:

.. code:: bash

   git tag  # to find tagged releases
   git checkout v0.3.3

Create a virtual environment just for the service, and install the code and
dependencies:

.. code:: bash

   python3 -m venv .venv --prompt="SBN Survey Image Service"
   source .venv/bin/activate
   python3 -m pip install -U pip setuptools wheel
   pip install .[recommended]


fitscut
^^^^^^^

The SIS uses the fitscut utility for generating cutouts and web (e.g., JPEG)
images.  Build and install it to the virtual environment.  There is a bash
script that can do this automatically for you:

.. code:: bash

   bash _install_fitscut


SIS configuration
^^^^^^^^^^^^^^^^^

The SIS is configured with a `.env` file.  Create a new configuration file,
populated with the SIS defaults:

.. code:: bash

   sbnsis env

Edit the `.env` file as needed, following the comments.

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

Start the service in production mode:

.. code:: bash

   sbnsis start

See below for how to add data to the database.  The service does not need to be
running to add data.


Adding archival data
--------------------

The `sbn_survey_image_service.data.add` sub-module is used to add image metadata
to the database. It harvests metadata from PDS4 labels, and saves it to the
database.  Also stored in the database is a URI specifying the location of the
label and data file.  This is all saved in a single table named "image":

.. code-block:: text

                                          Table "public.image"
         Column       |       Type        | Collation | Nullable |              Default              
   -------------------+-------------------+-----------+----------+-----------------------------------
   id                | integer           |           | not null | nextval('image_id_seq'::regclass)
   obs_id            | character varying |           | not null | 
   collection        | character varying |           | not null | 
   facility          | character varying |           | not null | 
   instrument        | character varying |           | not null | 
   data_product_type | character varying |           | not null | 
   calibration_level | integer           |           |          | 
   target            | character varying |           |          | 
   pixel_scale       | double precision  |           |          | 
   image_url         | character varying |           |          | 
   label_url         | character varying |           |          | 
   Indexes:
      "image_pkey" PRIMARY KEY, btree (id)
      "image_obs_id_key" UNIQUE CONSTRAINT, btree (obs_id)
      "ix_image_collection" btree (collection)
      "ix_image_facility" btree (facility)
      "ix_image_instrument" btree (instrument)
      "ix_image_obs_id" btree (obs_id) CLUSTER

The `add` sub-module provides a command-line script `sbnsis-add`. Run the script
with a label or directory to ingest.   For example, to recursively search a NEAT
survey directory for PDS4 image labels and data:

.. code:: bash

   sbnsis-add -r \
      /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata

The script will automatically create the database in case it does not exist.

The previous example is for a survey accessible via the local file system. As an
alternative, data may be served to the image service via HTTP(S). In this case,
the `sbnsis-add` script must still be run on locally accessible labels, but an
appropriate URL may be formed using the `--base-url` and `--strip-leading`
parameters:

.. code:: bash

   sbnsis-add -r \
      /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata \
      --base-url=https://sbnarchive.psi.edu/pds4/surveys \
      --strip-leading=/path/to/

For a summary of command-line parameters, use the `--help` option.

Due to survey-to-survey label differences, it is possible that the script will
not work with a previously untested data source. Edit the appropriate functions
in `sbn_survey_image_service/data/add.py`, e.g., `pds4_image()`. For example,
the NEAT survey PDS4 data set v1.0 does not have pixel scale in the label, so we
have hard coded it into the `pds4_image` function.

It is assumed that survey images are FITS-compatible with a World Coordinate
System defined for a standard sky reference frame (ICRS). The cutout service
uses the FITS header, not the PDS labels, to define the sub-frame. This is a
limitation from using fitscut, but this may be replaced in a future version.


Updating SBNSIS
---------------

For minor updates with SBNSIS that only require a restart of the server, first
tag a release on Github with the new version, e.g., v0.3.3.  Then, pull the
updated code and the new tag.  Upgrade the SIS and restart the service:

.. code:: bash

   git pull
   pip install -U -e .
   sbnsis restart


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
