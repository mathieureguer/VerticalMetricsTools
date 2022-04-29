# -*- coding: utf-8 -*-

from setuptools import setup


def readme():
  with open("README.md") as f:
    return f.read()


setup(name="VerticalMetricsTools",
      version="0.1",
      description="a little collection of tools to deal with font vertical metrics",
      long_description=readme(),
      classifiers=[
          "Development Status :: 4 - Beta",
          "License :: Other/Proprietary License",
          "Programming Language :: Python :: 2.7",
          "Topic :: Software Development :: Build Tools",
      ],
      author="Mathieu Reguer",
      author_email="mathieu.reguer@gmail.com",
      license="All rights reserved",
      packages=[
          "VerticalMetricsTools",
      ],
      entry_points="""
        [console_scripts]
        vertical_metrics_preview=VerticalMetricsTools.VerticalMetricsPreview:preview_vertical_metrics
        vertical_metrics_inject=VerticalMetricsTools.VerticalMetricsUpdate:vertical_metrics_inject_in_fonts_wrapper
        """,
      install_requires=[
          "fonttools",
          "click",
          "drawbot @ git+https://github.com/typemytype/drawbot",
          "pyaml"
      ],
      include_package_data=True,
      zip_safe=False)
