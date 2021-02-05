#!/usr/bin/env python3
from setuptools import setup, find_packages


if __name__ == "__main__":
    setup(
        name='sbn_survey_image_service',
        version='0.1.0-dev',
        description=('SBN Survey Image Service'),
        author="Michael S. P. Kelley",
        author_email="msk@astro.umd.edu",
        url="https://github.com/Small-Bodies-Node/sbn-survey-image-service",
        packages=find_packages(),
        install_requires=['Flask>=1.1.2', 'Flask-Cors>=3.0.10', 'gunicorn==20.0.4',
                          'connexion>=2.7.0', 'swagger-ui-bundle>=0.0.8', 'astropy>=4.2',
                          'pds4_tools==1.2', 'pds3==0.2.2', 'SQLAlchemy==1.3.5',
                          'python-dotenv==0.14.0', 'pytest-remotedata==0.3.2'],
    )
