from setuptools import setup, find_packages

setup(
    name = 'MimicDB',
    version = '1.0.2',
    packages = find_packages(),
    install_requires = ['boto>=2.32.1',],
    license = 'BSD',
    author = 'Nathan Cahill',
    author_email = 'nathan@nathancahill.com',
    url = 'https://github.com/nathancahill/mimicdb',
    description='Python implementation of MimicDB',
    long_description=open('README.txt').read(),
)
