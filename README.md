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


## Render pages
Render the blog into the output directory
```
make html
```

## Publish to GitHub
Copy the files in the output directory to the master branch (where my GitHub page displays from) and then push to github
```
ghp-import output -b master -p
```

## Post commit hook
I have now added a post-commit hook so my blog is updated everytime I make a commit on this branch!
