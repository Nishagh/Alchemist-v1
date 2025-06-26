"""
Alchemist Shared Libraries

This package contains common functionality shared across all Alchemist services.
"""

from setuptools import setup, find_packages

setup(
    name="alchemist-shared",
    version="1.0.0",
    description="Shared libraries for Alchemist AI platform",
    author="Alchemist Team",
    packages=find_packages(),
    install_requires=[
        "firebase-admin>=6.2.0",
        "google-cloud-firestore>=2.11.1",
        "google-cloud-storage>=2.10.0",
        "pydantic[email]>=2.4.2",
        "pydantic-settings>=2.0.0",
        "fastapi>=0.104.1",
        "python-jose[cryptography]>=3.3.0",
        "structlog>=23.1.0",
        "psutil>=5.9.0",
    ],
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta", 
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)