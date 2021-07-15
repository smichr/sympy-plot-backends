from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name = 'sympy_plot_backends',
    version = '0.12.3',
    description = 'Backends for plotting with SymPy',
    long_description = readme(),
    classifiers=[
        'Development Status :: Beta',
        'License :: GNU GPL v3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Mathematics, Engineering',
    ],
    keywords='sympy plot plotting backend plotly bokeh mayavi k3d panel',
    url = 'https://github.com/Davide-sd/sympy-plot-backends',
    author = 'Davide Sandona',
    author_email = 'sandona.davide@gmail.com',
    license='GNU GPL v3',
    packages = [
        'spb',
        'spb.backends'
        'spb.complex'
    ],
    include_package_data=True,
    zip_safe = False,
    install_requires = [
        "appdirs",
        "numpy",
        "scipy", # helps when lambdifying expressions
        "sympy",
        "matplotlib",
        "mergedeep",
        "ipympl",
        "plotly>=4.14.3",
        "colorcet",
        "param",
        "panel",
        "holoviews",
        "bokeh",
        "ipyevents",
        "PyQt5",
        # "mayavi",
        "k3d",
        "vtk", # needed for streamlines in k3d
        "cplot"
        # "pyvista",    # still immature jupyter notebook experience
        # "ipyvtklink"
    ]
)