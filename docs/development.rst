Development
===========

The bash script ``_setup_development`` will create and setup a virtual environment for development.  Use that now, or follow :doc:`install`, replacing the package installation step as directed below.

For development, install the package with the "dev", "test", and "docs" options. Also, it is beneficial to install the package in "editable" mode with the "-e" option to pip:

.. code:: bash

    pip install -e .[recommended,dev,test,docs]


Development mode
----------------

If you have ``nodemon`` globally installed, then you can develop your api code and have it automatically update on changes by running ``sbnsis start --dev``.  Otherwise, just run ``python -m sbn_survey_image_service.app``.


Testing
-------

Testing requires a test data set (images and PDS4 labels).  The test data set may be generated with the provided script:

.. code:: 

    $ python3 -m sbn_survey_image_service.data.test.generate
    usage: generate.py [-h] [--path PATH] [--add] [--exists] [--delete]
                    [--no-create-tables]

    Add/delete test data to/from SBN Survey Image Service database.

    options:
    -h, --help          show this help message and exit
    --path PATH         directory to which to save test data files (default:
                        /sbnsurveys/src/sbn-survey-image-
                        service/data/test)
    --add               add/create test data set (default: False)
    --exists            test for the existence of the test data set (default:
                        False)
    --delete            delete test data files and database rows (default:
                        False)
    --no-create-tables  do not attempt to create missing database tables
                        (default: False)

Run the `--add` option to generate the files and populate the database:

.. warning::

    `--add` will use the database configuration in your `.env` file.  It isn't harmful to add the test data set to a production database, but this may not be desired.  Testing data may be removed from the database with the `--delete` option.

.. code::

    $ python3 -m sbn_survey_image_service.data.test.generate --add
    INFO:__main__:Creating ~400 images and labels.
    INFO:SBN Survey Image Service:2024-11-08 09:06:47,245: Logging to /sbnsurveys/src/sbn-survey-image-service/logging/sbnsis.log
    INFO:SBN Survey Image Service:2024-11-08 09:06:47,245: Searching directory /sbnsurveys/src/sbn-survey-image-service/data/test
    INFO:SBN Survey Image Service:2024-11-08 09:06:47,912: Searched 1 directories, found 404 labels, 404 processed.
    INFO:__main__:Created and added 404 test images and their labels to the database.

The script `_test` will run the tests with `pytest`.  Coverage reports will be saved in HTML format to `htmlcov/`.  Tests requiring network access are run by default (using the --remote-data option to pytest).