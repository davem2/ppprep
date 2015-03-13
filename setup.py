from setuptools import setup, find_packages
setup(
  name          = 'dp2ppgen',
  author        = 'David Maranhao',
  author_email  = 'david.maranhao@gmail.com',
  license       = 'GPL3',
  description   = 'Translates pgdp.org formatted text files into ppgen syntax.',
  packages      = ['dp2ppgen'], # this must be the same as the name above
  version       = '0.2',
  url           = 'https://github.com/davem2/dp2ppgen', # use the URL to the github repo
  download_url  = 'https://github.com/davem2/dp2ppgen/tarball/0.2', # I'll explain this in a second
  keywords      = ['text', 'processing', 'book', 'gutenberg', 'distributedproofreaders'], # arbitrary keywords
  entry_points = {
      'console_scripts': [
          'dp2ppgen = dp2ppgen.dp2ppgen:main',
      ],
  },
  install_requires = [
    'docopt >= 0.6.1',
    'docutils >= 0.12',
  ]
)

