from setuptools import find_packages, setup

setup(
    name="django-mall-product",
    version="1.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "Django>=4.2",
        "django-app-organization>=1.0",
    ],
    author="Walker Chiu",
    author_email="chenjen.chiou@gmail.com",
    description="",
    classifiers=[
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
)
