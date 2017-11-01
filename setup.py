from setuptools import setup, find_packages

setup(
    name="HyperNote",
    version="0.1.0",
    packages=['hypernote', 'hypernote.frontend', 'hypernote.input',
              'hypernote.output'],
    install_requires=['python-dateutil'],
    entry_points={
        'console_scripts' : ['hnote = hypernote.frontend.main:main']},

    author='Matthew Bauer',
    author_email='bauer.s.matthew@gmail.com',
    description='A smart terminal-based notebook.',
    keywords='notebook workflow autofill',
    url='https://github.com/bauersmatthew/HyperNote'
)
