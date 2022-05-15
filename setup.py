import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pyaconf",
    version="0.7.2",
    author="ikh software, inc.",
    author_email="ikh@ikhsoftware.com",
    description=(
        "Yet another config library that is built around python dictionary "
        "and supports dynamic python, json, yaml, and ini formats "
        "with inheritance with Jinji2 templates"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ikhomyakov/pyaconf",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">= 3.7",
    install_requires=["pyyaml >= 5.1", "jinja2 >= 2.10"],
    scripts=["pyaconf_render"],
    project_urls={"Bug Reports": "https://github.com/ikhomyakov/pyaconf/issues"},
)
