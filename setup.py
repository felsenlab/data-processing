from setuptools import setup, find_packages

# Function to read requirements.txt
def read_requirements():
    with open("requirements.txt", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="data-processing",  # Replace with your package name
    version="0.1.0",  # Versioning: major.minor.patch
    author="Joshua B. Hunt",
    author_email="felsenlab@gmail.com",
    description="A Python package for extracting saccades from eye movement data",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/felsenlab/tata-processing",
    packages=find_packages(exclude=("tests", "docs")),  # Auto-discovers packages in the repo
    install_requires=read_requirements(),  # Read dependencies from requirements.txt
)