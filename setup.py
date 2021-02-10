import os
import setuptools

long_description = ''
if os.path.exists('README.md'):
    with open('README.md') as f:
        loag_description = f.read()

install_requires = []
if os.path.exists('requirements.txt'):
    with open('requirements.txt') as f:
        install_requires = [i.strip().split('==')[0] for i in f.readlines() if i.strip()]


setuptools.setup(
    name='timestamp',
    version='1.0.0',
    author='Brandon Jaus',
    author_email='brandon.jaus@gmail.com',
    description='tz aware timestamps made simple',
    long_description=long_description,
    log_description_content_type='text/markdown',
    packages=setuptools.find_packages(exclude=['tests']),
    install_requires=install_requires,
    tests_require=['pytest'],
    python_requires=">=3.7",
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
    ],
)
