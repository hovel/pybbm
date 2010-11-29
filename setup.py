from setuptools import setup

PACKAGE = 'pybbm'

setup(
    version = '0.1.8',
    description = 'PyBB Modified. Django forum application',
    author = 'Pavel Zhukov',
    author_email = 'gelios@gmail.com',
    name = 'pybbm',
    packages = ['pybb'],
    install_requires = [
            'django',
            'markdown',
            'postmarkup',
            'south',
            'pytils',
            'django-annoying',
            'sorl-thumbnail'
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
