from distutils.core import setup

setup(
    name='popcore',
    version='0.1',
    description='Core',
    author='Manfred Diaz',
    author_email='',
    url='https://www.python.org/sigs/distutils-sig/',
    package_dir={'': 'src'},
    packages=['popcore'],
    extras_require={
        'dev': [
            'pytest',
            'python-chess'
        ]
    }
)
