from setuptools import setup

setup(
    name='attachment-downloader',
    version='1.1.2',
    description='Simple tool for downloading email attachments for all emails in a given folder using an IMAP client.',
    long_description=open('README.rst').read(),
    author='James Ridgway',
    url='https://github.com/jamesridgway/attachment-downloader',
    license='MIT',
    packages=['attachment_downloader'],
    install_requires=["jinja2", "imbox"],
    entry_points = {
    "console_scripts": [ "attachment-downloader=attachment_downloader:main"]
    }
)
