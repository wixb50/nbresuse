from glob import glob
import setuptools

setuptools.setup(
    name="nbresuse",
    version='0.5.0',
    url="https://github.com/wixb50/nbresuse",
    author="wixb50",
    description="Simple Jupyter extension to show how much resources (RAM) your notebook is using",
    packages=setuptools.find_packages(),
    install_requires=[
        'psutil',
        'notebook',
    ],
    data_files=[
        ('share/jupyter/nbextensions/nbresuse', glob('nbresuse/static/*')),
        ('etc/jupyter/jupyter_notebook_config.d', ['nbresuse/etc/serverextension.json']),
        ('etc/jupyter/nbconfig/notebook.d', ['nbresuse/etc/nbextension.json'])
    ],
    zip_safe=False,
    include_package_data=True
)
