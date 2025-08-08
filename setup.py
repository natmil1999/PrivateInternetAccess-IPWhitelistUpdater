from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name = 'pia_whitelist_updater',
    version = '0.0.1',
    author = 'Nathan Miller',
    author_email = 'natmil1999@gmail.com',
    license = '<the license you chose>',
    description = 'A tool to keep the PIA VPN ip whitelist updated given on a set of domains to whitelist.',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = '<github url where the tool code will remain>',
    py_modules = ['pia_whitelist_cli', 'app'],
    packages = find_packages(),
    install_requires = ['click'],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX :: Linux",
    ],
    entry_points = '''
        [console_scripts]
        piawhitelistupdater=pia_whitelist_cli:cli
    '''
)