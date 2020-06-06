"""
Handles setup for the module
"""
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="logical-backup",
    version="1.0.0",
    author="Brett Ammeson",
    author_email="ammesonb@gmail.com",
    description=(
        "A utility for backing up and restoring"
        "files distributed across multiple hard drives"
    ),
    long_description=long_description,
    url="https://github.com/ammesonb/logical-backup",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)
