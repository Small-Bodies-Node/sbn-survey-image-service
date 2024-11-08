Adding archival data
====================

The ``sbn_survey_image_service.data.add`` sub-module is used to add image
metadata to the database. It harvests metadata from PDS4 labels, and saves it to
the database.  Also stored in the database is a URI specifying the location of
the label and data file.  This is all saved in a single table named "image":

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


Add script
----------

The a command-line script, ``sbnsis-add``, is provided for adding files. Run the
script with a label or directory to ingest.   For example, to recursively search
a NEAT survey directory for PDS4 image labels and data:

.. code:: bash

   sbnsis-add -r \
      /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata

The script will automatically create the database in case it does not exist.


Remotely served data
--------------------

The previous example is for a survey accessible via the local file system. As an
alternative, data may be served to the image service via HTTP(S). In this case,
the ``sbnsis-add`` script must still be run on locally accessible labels, but an
appropriate URL may be formed using the ``--base-url`` and ``--strip-leading``
parameters:

.. code:: bash

   sbnsis-add -r \
      /path/to/gbo.ast.neat.survey/data_geodss/g19960417/obsdata \
      --base-url=https://sbnarchive.psi.edu/pds4/surveys \
      --strip-leading=/path/to/

For a summary of command-line parameters, use the `--help` option.


Adapting for new surveys
------------------------

Due to survey-to-survey label differences, it is possible that the script will
not work with a previously untested data source. Edit the appropriate functions
in ``sbn_survey_image_service/data/add.py``, e.g., ``pds4_image()``. For
example, the NEAT survey PDS4 data set v1.0 does not have pixel scale in the
label, so we have hard coded it into the ``pds4_image`` function.

It is assumed that survey images are FITS-compatible with a World Coordinate
System defined for a standard sky reference frame (ICRS).
   
.. attention::

   The cutout service uses the FITS header, not the PDS labels, to define the sub-frame. Sourcing the
   WCS from the labels will be addressed in a future version.
