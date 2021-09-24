import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

project_id = "tns-energo-api"
setuptools.setup(
    name=project_id,
    version="0.0.4",
    author="Alexander Ryazanov",
    author_email="alryaz@xavux.com",
    description="TNS Energo API bindings for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alryaz/" + project_id,
    project_urls={
        "Bug Tracker": "https://github.com/alryaz/" + project_id + "/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        # "console_scripts": ["tns_energo=tns_energo.command_line:main"],
    },
    packages=setuptools.find_packages(exclude=("old", "tests")),
    python_requires=">=3.8",
)
