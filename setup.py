#!/usr/bin/env python3
"""
Setup script for Training Job Orchestrator
"""

from setuptools import setup, find_packages
from pathlib import Path
import os

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('#')
    ]

# Read version
version = "1.0.0"
version_file = Path(__file__).parent / "VERSION"
if version_file.exists():
    version = version_file.read_text(encoding='utf-8').strip()

setup(
    name="training-job-orchestrator",
    version=version,
    author="Your Organization",
    author_email="ml-team@example.com",
    description="Automated training job orchestrator with failure recovery and checkpoint restart",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/training-orchestrator",
    project_urls={
        "Bug Tracker": "https://github.com/yourorg/training-orchestrator/issues",
        "Documentation": "https://github.com/yourorg/training-orchestrator/blob/main/README.md",
        "Source Code": "https://github.com/yourorg/training-orchestrator",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Distributed Computing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Framework :: FastAPI",
    ],
    keywords="machine-learning training orchestration kubernetes docker mlops",
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.23.2",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pylint>=3.0.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "sphinx-autodoc-typehints>=1.24.0",
            "myst-parser>=2.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "grafana-api>=1.0.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "orchestrator=orchestrator:main",
            "orchestrator-api=api:main",
            "orchestrator-cli=cli:cli",
            "orchestrator-scheduler=scheduler:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "*.yaml",
            "*.yml", 
            "*.json",
            "*.sql",
            "*.md",
            "templates/*.html",
            "k8s/*.yaml",
        ],
    },
    data_files=[
        ("config", ["config.yaml"]),
        ("", [".env.example"]),
    ],
    zip_safe=False,
    platforms=["any"],
    license="MIT",
    test_suite="tests",
)