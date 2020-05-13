Raw blog content
================

This branch holds the blog posts in markdown and is used to generate the contents of the master branch, which is available at:
http://nathanwilliams.github.io

## Setup

- in the parent directory ```git clone https://github.com/getpelican/pelican-themes```
- Then run:
```
pelican-themes --install ../pelican-themes/foundation-default-colours --verbose
```

- in the parent directory
```git clone --recursive https://github.com/getpelican/pelican-plugins```

## Dev server
Start up a local server to check how everything looks
```
make devserver
```
Open: http://localhost:8000


## Build, publish onto the master branch and push the master branch to github
```bash
make html && ghp-import output -b master -p
```
