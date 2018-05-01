# JSCodeStyle - a lightweight style checker for JavaScript

## About

This tool reads your JavaScript code and provides suggestions on how
to improve the style for readability and consistency. It can also
check that your docstrings (JSDoc) explain the params and return
values of your JavaScript functions.

It doesn't use a JavaScript engine or browser engine to run the code,
it just reads the code like a human would.

Hopefully, this tool will be useful to people checking their own code,
as well as a sanity check for code review and/or continuous
integration tools.

It aims to be light and to avoid false positives. To take an analogy
from the Python world, it is more like pycodestyle than pylint.

## Installation

To install the application, run `python setup.py install`

After installing, you get two helper applications installed into `/usr/local/bin`:

* `jscodestype` - runs the linter and checks for errors
* `fixjsstyle` - tries to fix errors automatically

For backward compatibility, `gjslint` can also be used instead of
`jscodestype`.

Use `jscodestype --help` to see the full arguments available. Use
`fixjsstyle --dry-run` to see what it will change without actually
changing any files.

## Development

To run the tests, use `python setup.py test`

## History

gjslint stands for Google JavaScript Linter (I guess?). At some point
it was then branded as "Closure Linter", though it was never specific
to Closure code.

Google moved on to their more heavy and complicated linters written in
Java and node.js. So I picked it up.

I liked the lightweight approach of this tool, I don't need to install
half of NPM just to check if I have forgotten some semi-colons or made
some other basic style error.

It is still based on ES5, it doesn't yet do anything special for ES6,
although I hope to change that.
