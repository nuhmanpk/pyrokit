import pathlib
import setuptools

file = pathlib.Path(__file__).parent

README = (file / "README.md").read_text()

requirements = (file / "requirements.txt").read_text().splitlines()


setuptools.setup(
    name="pyrokit",
    version="0.0.1",
    author="Nuhman Pk",
    author_email="nuhmanpk7@gmail.com",
    long_description = README,
    long_description_content_type = "text/markdown",
    description="The Complete Bot Builder Kit for Pyrogram Bots: Build, Enhance, and Scale with Ease",
    license="MIT",
    url="https://github.com/nuhmanpk/pyrokit",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(include=['pyrokit']),
    install_requires=requirements,
    python_requires=">=3.10",
    project_urls={
        'Documentation': 'https://github.com/nuhmanpk/pyrokit/blob/main/README.md',
        'Funding': 'https://github.com/sponsors/nuhmanpk',
        'Source': 'https://github.com/nuhmanpk/pyrokit/',
        'Tracker': 'https://github.com/nuhmanpk/pyrokit/issues',
    },
    
)
