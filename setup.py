from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.readlines()

with open('README.md') as f:
    long_description = f.read()

setup(
    name='exams2anki',
    version='1.1.0',
    author='Guilherme Caulada',
    author_email='guilherme.caulada@gmail.com',
    url='https://github.com/Sighmir/exams2anki',
    description='Convert ExamTopics pages to Anki decks!',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='AGPL-3.0',
    package_dir={'': 'src'},
    data_files=[('templates', [
        'templates/backside.html',
        'templates/frontside.html',
        'templates/style.css',
    ])],
    py_modules=['exams2anki'],
    entry_points={
        'console_scripts': [
            'exams2anki = exams2anki:main'
        ]
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ),
    keywords='anki examtopics exam certification cert sighmir',
    install_requires=requirements,
    zip_safe=False
)
