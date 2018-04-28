#!/usr/bin/env python
# Copyright 2018 The JsCodeStyle Authors.
# Copyright 2007 The Closure Linter Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Checks JavaScript files for common style guide violations.

gjslint.py is designed to be used as a PRESUBMIT script to check for javascript
style guide violations.  As of now, it checks for the following violations:

  * Missing and extra spaces
  * Lines longer than 80 characters
  * Missing newline at end of file
  * Missing semicolon after function declaration
  * Valid JsDoc including parameter matching

Someday it will validate to the best of its ability against the entirety of the
JavaScript style guide.

This file is a front end that parses arguments and flags.  The core of the code
is in tokenizer.py and checker.py.
"""

import errno
import itertools
import os
import platform
import sys
import time
import glob
import os
import re



import gflags as flags


from jscodestyle.errorrecord import check_path
from jscodestyle import runner
from jscodestyle.common import erroraccumulator

# Attempt import of multiprocessing (should be available in Python 2.6 and up).
try:
    import multiprocessing
except ImportError:
    multiprocessing = None

FLAGS = flags.FLAGS
flags.DEFINE_boolean('unix_mode', False,
                     'Whether to emit warnings in standard unix format.')
flags.DEFINE_boolean('beep', True, 'Whether to beep when errors are found.')
flags.DEFINE_boolean('time', False, 'Whether to emit timing statistics.')
flags.DEFINE_boolean('quiet', False, 'Whether to minimize logged messages. '
                     'Most useful for per-file linting, such as that '
                     'performed by the presubmit linter service.')
flags.DEFINE_boolean('check_html', False,
                     'Whether to check javascript in html files.')
flags.DEFINE_boolean('summary', False,
                     'Whether to show an error count summary.')
flags.DEFINE_list('additional_extensions', None, 'List of additional file '
                  'extensions (not js) that should be treated as '
                  'JavaScript files.')
flags.DEFINE_boolean('multiprocess',
                     platform.system() == 'Linux' and bool(multiprocessing),
                     'Whether to attempt parallelized linting using the '
                     'multiprocessing module.  Enabled by default on Linux '
                     'if the multiprocessing module is present (Python 2.6+). '
                     'Otherwise disabled by default. '
                     'Disabling may make debugging easier.')
flags.DEFINE_list('limited_doc_files', ['dummy.js', 'externs.js'],
                  'List of files with relaxed documentation checks. Will not '
                  'report errors for missing documentation, some missing '
                  'descriptions, or methods whose @return tags don\'t have a '
                  'matching return statement.')
flags.DEFINE_boolean('error_trace', False,
                     'Whether to show error exceptions.')
flags.DEFINE_list('closurized_namespaces', '',
                  'Namespace prefixes, used for testing of'
                  'goog.provide/require')
flags.DEFINE_list('ignored_extra_namespaces', '',
                  'Fully qualified namespaces that should be not be reported '
                  'as extra by the linter.')
flags.DEFINE_list('custom_jsdoc_tags', '', 'Extra jsdoc tags to allow')

# TODO(user): When flipping this to True, remove logic from unit tests
# that overrides this flag.
flags.DEFINE_boolean('dot_on_next_line', False, 'Require dots to be'
                     'placed on the next line for wrapped expressions')

flags.DEFINE_boolean('check_trailing_comma', False, 'Check trailing commas'
                     ' (ES3, not needed from ES5 onwards)')
flags.DEFINE_boolean('debug_indentation', False,
                     'Whether to print debugging information for indentation.')
flags.DEFINE_integer('max_line_length', 80, 'Maximum line length allowed '
                     'without warning.', lower_bound=1)

flags.DEFINE_multistring(
    'recurse',
    None,
    'Recurse in to the subdirectories of the given path',
    short_name='r')
flags.DEFINE_list(
    'exclude_directories',
    ('_demos'),
    'Exclude the specified directories (only applicable along with -r or '
    '--presubmit)',
    short_name='e')
flags.DEFINE_list(
    'exclude_files',
    ('deps.js'),
    'Exclude the specified files',
    short_name='x')
flags.DEFINE_boolean('jsdoc', True,
                     'Whether to report errors for missing JsDoc.')
flags.DEFINE_list('disable', None,
                  'Disable specific error. Usage Ex.: gjslint --disable 1,'
                  '0011 foo.js.')

flags.ADOPT_module_key_flags(runner)


GJSLINT_ONLY_FLAGS = ['--unix_mode', '--beep', '--nobeep', '--time',
                      '--check_html', '--summary', '--quiet']


def _multiprocess_check_paths(paths):
    """Run _check_path over mutltiple processes.

    Tokenization, passes, and checks are expensive operations.  Running in a
    single process, they can only run on one CPU/core.  Instead,
    shard out linting over all CPUs with multiprocessing to parallelize.

    Args:
      paths: paths to check.

    Yields:
      errorrecord.ErrorRecords for any found errors.
    """

    pool = multiprocessing.Pool()

    path_results = pool.imap(_check_path, paths)
    for results in path_results:
        for result in results:
            yield result

    # Force destruct before returning, as this can sometimes raise spurious
    # "interrupted system call" (EINTR), which we can ignore.
    try:
        pool.close()
        pool.join()
        del pool
    except OSError as err:
        if err.errno is not errno.EINTR:
            raise err


def _check_paths(paths):
    """Run _check_path on all paths in one thread.

    Args:
      paths: paths to check.

    Yields:
      errorrecord.ErrorRecords for any found errors.
    """

    for path in paths:
        results = _check_path(path)
        for record in results:
            yield record


def _check_path(path):
    return check_path(
        path,
        flags.FLAGS.unix_mode,
        flags.FLAGS.limited_doc_files,
        flags.FLAGS.error_trace,
        flags.FLAGS.closurized_namespaces,
        flags.FLAGS.ignored_extra_namespaces,
        flags.FLAGS.custom_jsdoc_tags,
        flags.FLAGS.dot_on_next_line,
        flags.FLAGS.check_trailing_comma,
        flags.FLAGS.debug_indentation,
        flags.FLAGS.jsdoc,
        flags.FLAGS.disable,
        flags.FLAGS.max_line_length)


def _get_file_paths(argv):
    """NOTE: This doesn't seem to be used anywhere?"""
    suffixes = ['.js']
    if FLAGS.additional_extensions:
        suffixes += ['.%s' % ext for ext in FLAGS.additional_extensions]
    if FLAGS.check_html:
        suffixes += ['.html', '.htm']
    return GetFileList(argv, 'JavaScript', suffixes)


# Error printing functions


def _print_file_summary(paths, records):
    """Print a detailed summary of the number of errors in each file."""

    paths = list(paths)
    paths.sort()

    for path in paths:
        path_errors = [e for e in records if e.path == path]
        print '%s: %d' % (path, len(path_errors))


def _print_file_separator(path):
    print '----- FILE  :  %s -----' % path


def _print_summary(paths, error_records):
    """Print a summary of the number of errors and files."""

    error_count = len(error_records)
    all_paths = set(paths)
    all_paths_count = len(all_paths)

    if error_count is 0:
        print '%d files checked, no errors found.' % all_paths_count

    new_error_count = len([e for e in error_records if e.new_error])

    error_paths = set([e.path for e in error_records])
    error_paths_count = len(error_paths)
    no_error_paths_count = all_paths_count - error_paths_count

    if (error_count or new_error_count) and not FLAGS.quiet:
        error_noun = 'error' if error_count == 1 else 'errors'
        new_error_noun = 'error' if new_error_count == 1 else 'errors'
        error_file_noun = 'file' if error_paths_count == 1 else 'files'
        ok_file_noun = 'file' if no_error_paths_count == 1 else 'files'
        print('Found %d %s, including %d new %s, in %d %s (%d %s OK).' %
              (error_count,
               error_noun,
               new_error_count,
               new_error_noun,
               error_paths_count,
               error_file_noun,
               no_error_paths_count,
               ok_file_noun))


def _print_error_records(error_records):
    """Print error records strings in the expected format."""

    current_path = None
    for record in error_records:

        if current_path != record.path:
            current_path = record.path
            if not FLAGS.unix_mode:
                _print_file_separator(current_path)

        print record.error_string


def _format_time(duration):
    """Formats a duration as a human-readable string.

    Args:
      duration: A duration in seconds.

    Returns:
      A formatted duration string.
    """
    if duration < 1:
        return '%dms' % round(duration * 1000)
    return '%.2fs' % duration


def main(argv=None):
    """Main function.

    Args:
      argv: Sequence of command line arguments.
    """
    if argv is None:
        argv = flags.FLAGS(sys.argv)

    if FLAGS.time:
        start_time = time.time()

    # Emacs sets the environment variable INSIDE_EMACS in the subshell.
    # Request Unix mode as emacs will expect output to be in Unix format
    # for integration.
    # See https://www.gnu.org/software/emacs/manual/html_node/emacs/
    # Interactive-Shell.html
    if 'INSIDE_EMACS' in os.environ:
        FLAGS.unix_mode = True

    suffixes = ['.js']
    if FLAGS.additional_extensions:
        suffixes += ['.%s' % ext for ext in FLAGS.additional_extensions]
    if FLAGS.check_html:
        suffixes += ['.html', '.htm']
    paths = GetFileList(argv, 'JavaScript', suffixes)

    if FLAGS.multiprocess:
        records_iter = _multiprocess_check_paths(paths)
    else:
        records_iter = _check_paths(paths)

    records_iter, records_iter_copy = itertools.tee(records_iter, 2)
    _print_error_records(records_iter_copy)

    error_records = list(records_iter)
    _print_summary(paths, error_records)

    exit_code = 0

    # If there are any errors
    if error_records:
        exit_code += 1

    # If there are any new errors
    if [r for r in error_records if r.new_error]:
        exit_code += 2

    if exit_code:
        if FLAGS.summary:
            _print_file_summary(paths, error_records)

        if FLAGS.beep:
            # Make a beep noise.
            sys.stdout.write(chr(7))

        # Write out instructions for using fixjsstyle script to fix some of the
        # reported errors.
        fix_args = []
        for flag in sys.argv[1:]:
            for go_flag in GJSLINT_ONLY_FLAGS:
                if flag.startswith(go_flag):
                    break
            else:
                fix_args.append(flag)

        if not FLAGS.quiet:
            print """
      Some of the errors reported by GJsLint may be auto-fixable using the
      command fixjsstyle. Please double check any changes it makes and report
      any bugs. The command can be run by executing:

      fixjsstyle %s """ % ' '.join(fix_args)

    if FLAGS.time:
        print 'Done in %s.' % _format_time(time.time() - start_time)

    sys.exit(exit_code)



def MatchesSuffixes(filename, suffixes):
    """Returns whether the given filename matches one of the given suffixes.

    Args:
      filename: Filename to check.
      suffixes: Sequence of suffixes to check.

    Returns:
      Whether the given filename matches one of the given suffixes.
    """
    suffix = filename[filename.rfind('.'):]
    return suffix in suffixes


def _GetUserSpecifiedFiles(argv, suffixes):
    """Returns files to be linted, specified directly on the command line.

    Can handle the '*' wildcard in filenames, but no other wildcards.

    Args:
      argv: Sequence of command line arguments. The second and following arguments
        are assumed to be files that should be linted.
      suffixes: Expected suffixes for the file type being checked.

    Returns:
      A sequence of files to be linted.
    """
    files = argv[1:] or []
    all_files = []
    lint_files = []

     # Perform any necessary globs.
    for f in files:
        if f.find('*') != -1:
            for result in glob.glob(f):
                all_files.append(result)
        else:
            all_files.append(f)

    for f in all_files:
        if MatchesSuffixes(f, suffixes):
            lint_files.append(f)
    return lint_files


def _GetRecursiveFiles(suffixes):
    """Returns files to be checked specified by the --recurse flag.

    Args:
      suffixes: Expected suffixes for the file type being checked.

    Returns:
      A list of files to be checked.
    """
    lint_files = []
    # Perform any request recursion
    if FLAGS.recurse:
        for start in FLAGS.recurse:
            for root, subdirs, files in os.walk(start):
                for f in files:
                    if MatchesSuffixes(f, suffixes):
                        lint_files.append(os.path.join(root, f))
    return lint_files


def GetAllSpecifiedFiles(argv, suffixes):
    """Returns all files specified by the user on the commandline.

    Args:
      argv: Sequence of command line arguments. The second and following arguments
        are assumed to be files that should be linted.
      suffixes: Expected suffixes for the file type

    Returns:
      A list of all files specified directly or indirectly (via flags) on the
      command line by the user.
    """
    files = _GetUserSpecifiedFiles(argv, suffixes)

    if FLAGS.recurse:
        files += _GetRecursiveFiles(suffixes)

    return FilterFiles(files)


def FilterFiles(files):
    """Filters the list of files to be linted be removing any excluded files.

    Filters out files excluded using --exclude_files and  --exclude_directories.

    Args:
      files: Sequence of files that needs filtering.

    Returns:
      Filtered list of files to be linted.
    """
    num_files = len(files)

    ignore_dirs_regexs = []
    for ignore in FLAGS.exclude_directories:
        ignore_dirs_regexs.append(re.compile(r'(^|[\\/])%s[\\/]' % ignore))

    result_files = []
    for f in files:
        add_file = True
        for exclude in FLAGS.exclude_files:
            if f.endswith('/' + exclude) or f == exclude:
                add_file = False
                break
        for ignore in ignore_dirs_regexs:
            if ignore.search(f):
                # Break out of ignore loop so we don't add to
                # filtered files.
                add_file = False
                break
        if add_file:
            # Convert everything to absolute paths so we can easily remove duplicates
            # using a set.
            result_files.append(os.path.abspath(f))

    skipped = num_files - len(result_files)
    if skipped:
        print 'Skipping %d file(s).' % skipped

    return set(result_files)


def GetFileList(argv, file_type, suffixes):
    """Parse the flags and return the list of files to check.

    Args:
      argv: Sequence of command line arguments.
      suffixes: Sequence of acceptable suffixes for the file type.

    Returns:
      The list of files to check.
    """
    return sorted(GetAllSpecifiedFiles(argv, suffixes))


def IsEmptyArgumentList(argv):
    return not (len(argv[1:]) or FLAGS.recurse)



if __name__ == '__main__':
    main()
