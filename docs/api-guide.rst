API User's Guide
================

The SBN SIS is deployed and available at the `Small-Bodies Node <https://sbnsurveys.astro.umd.edu/api/ui>`_
.  Two data sets are available:

* Near-Earth Asteroid Tracking (NEAT) survey
* Asteroid-Terrestrial Last Alert System (ATLAS) survey

This guide explains how to use the SIS to access these data.  You may already
know the data product you are interested in, or you may want to search the
database to inspect it's holdings.

The examples below use the ``curl`` program to display the responses from the
API.


Why search the database?
------------------------

The primary means for accessing SBN's survey holdings is through the `CATCH
tool <https://catch.astro.umd.edu/>`_.  CATCH can search for known comets,
asteroids, or fixed (Celestial) targets.  However, in some cases a user may want
to identify data related to the CATCH results, or may be curious about the
general state of the data archived and available for a survey.  In these cases,
the SIS database may be helpful.


Summarize by collection and facility
------------------------------------

The ``/summary`` API endpoint returns a list of all data organized by collection
and facility:

.. code:: bash

    $ curl https://sbnsurveys.astro.umd.edu/api/summary
    [
        {
            "collection": "test-collection",
            "count": 808,
            "facility": "test-facility",
            "instrument": "test-instrument"
        },
        {
            "collection": "urn:nasa:pds:gbo.ast.atlas.survey.234:58475",
            "count": 1027,
            "facility": "ATLAS MLO 0.5m Telescope",
            "instrument": "STA-1600 10.5x10.5k CCD"
        },
        {
            "collection": "urn:nasa:pds:gbo.ast.atlas.survey.234:58476",
            "count": 134,
            "facility": "ATLAS HKO 0.5m Telescope",
            "instrument": "STA-1600 10.5x10.5k CCD"
        },
        {
            "collection": "urn:nasa:pds:gbo.ast.atlas.survey.234:58476",
            "count": 994,
            "facility": "ATLAS MLO 0.5m Telescope",
            "instrument": "STA-1600 10.5x10.5k CCD"
        },
        ...
    ]

In the above snippet, we see a "test-collection" data set that is used for
internal testing, and the first three ATLAS entries.  The first is the Mauna Loa
telescope data from the "urn:nasa:pds:gbo.ast.atlas.survey.234:58475" data
collection.  See the ATLAS documentation for naming schemes.  The next two are
data from another collection (...58476), separated into the Mauna Loa and
Haleakala telescopes.  There are 994 data products from the Mauna Loa telescope
in the "urn:nasa:pds:gbo.ast.atlas.survey.234:58476" data collection.

Find data products in a collection
----------------------------------



How to get an image?
How to get a PDS label?
How to get an image cutout?
