from setuptools import setup, find_packages

setup(
    name="evrmore-rpc",
    version="1.2.0",  # Incrementing version for new features
    author="Manticore Technologies",
    author_email="dev@manticore.tech",
    description="A comprehensive, typed Python wrapper for Evrmore blockchain with ZMQ and WebSockets support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/manticore-projects/evrmore-rpc",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=10.0.0",
        "pydantic>=2.0.0",
        "pyzmq>=25.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "websockets": [
            "websockets>=11.0.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
        ],
        "full": [
            "websockets>=11.0.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "evrmore-rpc=evrmore_rpc.cli:main",
            "evrmore-interactive=evrmore_rpc.interactive:main",
        ],
    },
) 