# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/setup.py
# Description: Package setup configuration for MyRAGDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="myragdb",
    version="0.1.0",
    author="Libor Ballaty",
    author_email="libor@arionetworks.com",
    description="Hybrid search system combining Keyword (Meilisearch) and vector embeddings for code/documentation discovery",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lballaty/myragdb",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "chromadb>=0.4.22",
        "sentence-transformers>=2.3.1",
        "torch>=2.1.2",
        "python-magic>=0.4.27",
        "chardet>=5.2.0",
        "watchdog>=3.0.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "structlog>=24.1.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "httpx>=0.26.0",
        "prometheus-client>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "httpx>=0.26.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "myragdb=myragdb.cli:cli",
        ],
    },
)
