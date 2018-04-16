# JSCodeStyle - a lightweight style checker for JavaScript

## Installation

To install the application, run `python setup.py install`

After installing, you get two helper applications installed into `/usr/local/bin`:

* `gjslint.py` - runs the linter and checks for errors
* `fixjsstyle.py` - tries to fix errors automatically

## History

gjslint stands for Google Linter (I guess?). At some point it was then
branded as "Closure Linter", though it was never specific to Closure
code.

Google moved on to their more heavy and complicated linters written in
Java and node.js. So I picked it up.

I liked the lightweight approach of this tool, I don't need to install
half of NPM just to check if I have forgotten some semi-colons or made
some basic other style error.

It doesn't use a JavaScript engine or browser engine to run the code,
it just reads the code like a human would.

To take an analogy from the Python world, it is more like pycodestyle
than pylint.

It is still based on ES5, it doesn't yet do anything special for ES6,
although I hope to change that.

Hopefully, this tool will be useful to people checking their own code,
as well as a sanity check for code review/continuous tools.
