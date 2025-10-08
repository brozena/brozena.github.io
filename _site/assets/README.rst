.. image:: https://gitlab.com/saeed-abdullah/oysterpail/badges/master/pipeline.svg
    :alt: Build status
    :target: https://gitlab.com/saeed-abdullah/oysterpail/commits/master

.. image:: https://gitlab.com/saeed-abdullah/oysterpail/badges/master/coverage.svg
    :alt: Coverage report
    :target: https://gitlab.com/saeed-abdullah/oysterpail/commits/master

*OysterPail* is an application for parsing and analyzing online interaction (behavior)
data. We are mostly focusing on parsing Google Takeout [#name]_ data for now.

Installation
============

*OysterPail* uses `Poetry`_  for project management.

* Follow the installation steps for Poetry here: `https://github.com/sdispater/poetry/blob/master/README.md <https://github.com/sdispater/poetry/blob/master/README.md>`_

* Clone the project: ``git clone https://gitlab.com/saeed-abdullah/oysterpail.git``

* ``cd`` to the project root

* run ``poetry install``

It should address all dependencies and install *OysterPail*. You can check by
running the tests (``pytest`` at the project root).

Development
===========

Localized timestamps
--------------------
Some data entries only retains Unix timestamps. We often want to convert this to
a user's local time. Determining local time can be complicated due to daylight
savings time or a user's travel. One way of keeping track of local timezone is
to use the timestamp of sent emails.

The `oysterpail.takeout.localtz` module provides these functionalities. There
are two steps:

1. First, you will need to generate timezone changes as inferred from sent emails.
   You can do this by running the `localtz.py` from terminal:

   `> python3 localtz.py parse mail Sent.mbox timezone_output.pickle`

   The sorted timezone changes will be saved as `timezone_output.pickle` after running
   this command.

2. In your parsing code, you will need to load the pickle file. You can use command-line
   arguments to point the pickle file:

    `> python3 browser.py input-file output-file timezone_output.pickle`

Then, you will need to:

    * call `localtz.init` with the pickle file path location (i.e.,
      `localtz.init(timezone_output.pickle)` in this example)
    * use `localtz.get_tz_trail()` to get the `TimeZoneTrail` instance

In other words, the code in  `browser.py` will look something similar to:

.. code-block::

    from oysterpail.takeout import localtz
    import sys
    import pickle

    def main(input_f: PathLike, output_f: PathLike, tz_trail_f: PathLike):
        # handle input, output, and parser ...

        # init localtz
        localtz.init(tz_trail_f)

        # get TimeZoneTrail instance from the pickle file
        tz_trail = localtz.get_tz_trail()

    # handle command line arguments
    if __name__ == "__main__":
        args = sys.argv[1:]
        input_f = args[0]
        output_f = args[1]
        tz_trail_f = args[2]
        main(Path(input_f), Path(output_f), Path(tz_trail_f))

3. Now, you can use the returned instance in your code to convert Unix
   timestamps (or any `datetime` object) to a user's current local time:

.. code-block::

    # now, you can use the object to convert timestamps to local timezone
    localized_ts = localtz.get_tz_trail().localize(1579280039)

    # you can also convert other non-naive datetime objects to local timezone
    dt_utc = dt.datetime(2020, 1, 17, tzinfo=pytz.utc)  # in utc
    localized_dt = localtz.get_tz_trail().localize(dt_utc)

    # it can also handle string formatted dates using dateutil.parse
    localized_dt2 = localtz.get_tz_trail().localize("2020-01-17T00:00:00-04:56")


Pre commit hooks
----------------

*OysterPail* uses:

* `black <https://github.com/psf/black>`_ for code formatting
* `flake8 <http://flake8.pycqa.org/en/latest/index.html>`_ for style guide
* `Mypy <https://mypy.readthedocs.io/en/latest/index.html>`_ for type checking
* `pre-commit <https://github.com/pre-commit/pre-commit>`_ for ensuring code consistency

For developing, please ensure that pre-commit hooks are installed properly.
That is, run the following command as you set up your developing environment:
``pre-commit install``. It will initiate the pre-commit framework and checks
against each commit.

Testing
-------
We are aiming for pretty good test coverage for the codebase. Please
write and maintain test cases for meaningful changes.

.. _Poetry: https://github.com/sdispater/poetry/blob/master/README.md

.. rubric:: Footnotes

.. [#name] The initial focus on Google *Takeout* explains the project name
    `OysterPail <https://en.wikipedia.org/wiki/Oyster_pail>`_.
