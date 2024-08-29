Installation and Setup
======================

Select and install your choice of database backend, either sqlite3 or
postgresql.  If using postgresql, it is recommended to have two separate users
with access: one that can perform database maintenance (e.g., INSERT and UPDATE
permissions), and another that will be limited to read-only access.


Requirements
------------

All python requirements are managed by the pyproject.toml file and automatically
installed with pip below.  In addition,
[libtool](https://www.gnu.org/software/libtool/) and fitscut are needed.  Follow
your typical system installation instructions for libtool.  The installation of
fitscut is described below.


SBN SIS
-------

   The steps below are mostly covered by the ``_setup_production.sh`` script.
   Follow along below, or run that script now.

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
-------

The SIS uses the fitscut utility for generating cutouts and web (e.g., JPEG)
images.  Build and install it to the virtual environment.  There is a bash
script that can do this automatically for you:

.. code:: bash

   bash _install_fitscut


SIS configuration
-----------------

The SIS is configured with a ``.env`` file.  Create a new configuration file,
populated with the SIS defaults:

.. code:: bash

   sbnsis env

Edit the ``.env`` file as needed, following the comments.

Running the service is covered in :doc:`service`.