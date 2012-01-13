from setuptools import setup, find_packages

setup(
    version = '0.6.1',
    description = 'PyBB Modified. Django forum application',
    long_description = open('README.rst').read(),
    author = 'Pavel Zhukov',
    author_email = 'gelios@gmail.com',
    name = 'pybbm',
    packages = find_packages(),
    include_package_data = True,
    package_data = {'': ['pybb/templates', 'pybb/static']},
    install_requires = [
            'django',
            'markdown',
            'postmarkup',
            'south',
            'pytils',
            'django-annoying',
            'sorl-thumbnail',
            'django-pure-pagination'
            ],

    license = "BSD",
    keywords = "django application forum board",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
