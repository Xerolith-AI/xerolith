from setuptools import setup, find_packages

setup(
    name="xerolith",
    version="1.0.0",
    author="Tyler Love",
    description="Autonomous AI with persistent memory that never forgets",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Xerolith-AI/xerolith",
    packages=find_packages(include=["xerolith", "xerolith.*"]),
    package_data={
        "xerolith": ["**/*.py"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "python-dotenv>=0.20.0",
    ],
)
