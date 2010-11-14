from setuptools import setup

PACKAGE = 'pybb'

setup(
    version = '0.1.6',
    description = 'Django forum application',
    author = 'Pavel Zhukov',
    author_email = 'gelios@gmail.com',
    name = 'pybb',
    packages = ['pybb'],
    install_requires = [
            'django',
            'markdown',
            'south',
            'django-common',
            'BeautifulSoup',
            'pytils',
            'django-annoying',
            'django-bbmarkup',
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
