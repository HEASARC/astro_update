Using Astro-Update software to update the HEASARC Astro-update page
====================================================================

From the command line, run ``update_astroupdate`` ::

    % update_astroupdate --help
    usage: update_astroupdate [-h] [--DefDir DEFDIR] [--clobber]
                              [--DefFile DEFFILE] [--outdir OUTDIR]
                              [--outname OUTNAME]

    updates the astro-update web page

    optional arguments:
      -h, --help         show this help message and exit
      --DefDir DEFDIR    location of the astro-update definitions database file
                         (default =
                         /software/github/heasarc/astro_update/definitions)
      --clobber          overwrite output directory
      --DefFile DEFFILE  name of astro-update definitions database file (default =
                         astroupdate_defs_MASTER.json)
      --outdir OUTDIR    location of output html file (default =
                         /software/github/heasarc/astro_update/html)
      --outname OUTNAME  name of output astroupdate html file (default = astro-
                         update.html)

``update_astroupdate`` sets the path to the  astro-update definitions file, the astro_update file name (which generally should be
``astroupdate_defs_MASTER.json``, though other definition files, for example from the last run of ``update_astroupdate``,
could be used), and the path to the output directory and the output file name (if the default filename is used you probably need to
set --clobber = True to overwrite the file).

Running ``update_astroupdate`` will:

    * create a new json astro_update definitions file in the ``DEFDIR`` directory, with a name of the form ``astroupdate_defs_20170511.json``

    * create a new html file in the ``OUTDIR`` (need to set ``--clobber=True`` if the file exists and you want to overwrite it).

The  command ``update_astroupdate`` is a simple wrapper to the python function ``update_astroupdate(defdir=defdir, deffile=deffile, clobber=clobber)``
in the ``astroupdate`` module.  The python function ``update_astroupdate(defdir=defdir, deffile=deffile, clobber=clobber)`` does the following:

    * runs ``read_au_defs()`` to create an astro-update pandas dataframe from the specified astro-update json definitions file

    * gets all the software names from the dataframe; these are the names of the software being monitored by astro-update

    * for each software name in the dataframe, gets the current version and current release date from the software maintainer's website
      using ``get_au_curvers()``

    * after that, creates a new json definitions file using the current values of version and release date for each software package

    * then runs ``make_astroupdate_page()`` to actually make the astro-update webpage (stored in the directory specified by the ``outdir``
      parameter)
