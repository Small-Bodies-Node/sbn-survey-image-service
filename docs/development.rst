Development
===========

The bash script ``_setup_development`` will create and setup a virtual
environment for development.  Use that now, or follow :doc:`install`, replacing
the package installation step as directed below.

For development, install the package with the "dev", "test", and "docs" options.
Also, it is beneficial to install the package in "editable" mode with the "-e"
option to pip:

.. code:: bash

    pip install -e .[recommended,dev,test,docs]

If you have ``nodemon`` globally installed, then you can develop your api code
and have it automatically update on changes by running ``sbnsis start --dev``.
Otherwise, just run ``python -m sbn_survey_image_service.app``.
