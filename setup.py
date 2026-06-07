from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="factura-co",
    version="0.2.0",
    author="Brausin",
    author_email="juansvargasb@gmail.com",
    description="Calculadora de retenciones, aportes y generador de documentos de cobro para freelancers colombianos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Brausin/factura-co",
    project_urls={
        "Bug Tracker": "https://github.com/Brausin/factura-co/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: Spanish",
        "Topic :: Office/Business :: Financial",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "tabulate>=0.9.0",
    ],
    extras_require={
        "pdf": ["fpdf2>=2.7.0"],
        "dev": ["pytest>=7.0.0"],
    },
    entry_points={
        "console_scripts": [
            "factura-co=factura_co.calculadora:main",
        ],
    },
)
