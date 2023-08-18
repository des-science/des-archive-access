# des-archive-access

[![pre-commit](https://github.com/des-science/des-archive-access/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/des-science/des-archive-access/actions/workflows/pre-commit.yml) [![tests](https://github.com/des-science/des-archive-access/actions/workflows/tests.yml/badge.svg)](https://github.com/des-science/des-archive-access/actions/workflows/tests.yml)

tools for accessing the DES data archive at FNAL

## Installation

**Right now this package is in its alpha state and so all installation is directly from the `main` branch!**

### PyPI

Install the package and dependencies directly from GitHub with `pip`

```bash
pip install git+https://github.com/fermitools/htgettoken.git
pip install git+https://github.com/des-science/des-archive-access.git
```

### conda

Install the dependencies with `conda` and then install the tool with `pip`

```bash
git clone https://github.com/des-science/des-archive-access.git
cd des-archive-access
conda install --file requirements.txt --file requirements-dev.txt
pip install --no-deps --no-build-isolation .
cd -
```

You will need at least Python 3.8.

## Instructions for Generating an OIDC Token for FNAL dCache (2023/08/18)

In order to download files, you need to generate an OIDC token. To make the token, do the following.

1. Run the command line tool `des-archive-access-make-token`.
2. You will be redirected to a CILogon website.
3. Login with your **FNAL SERVICES** account. You may be offered other identity providers, but you have to use the FNAL one!

The token will be stored in the `~/.des_archive_access/` directory in your home area. **Make the sure the permissions on this directory are `700` via `chmod 700 ~/.des_archive_access/`.** You can change this location by setting the environment variable `DES_ARCHIVE_ACCESS_DIR`.

## Usage

### Downloading the Archive Metadata

Before you can query the file archive metadata, you need to download the metadata database (roughly 8GB) via the `des-archive-access-download-metadata`
command. This command will put the data in your home area. If you'd like to specify a different path to the DB, set it via the environment variable `DES_ARCHIVE_ACCESS_DB` like this

```bash
$ export DES_ARCHIVE_ACCESS_DB=/my/metadata.db
```

### Querying the Archive Metadata

Then you can use the `des-archive-access` command to interact with the metadata.

```bash
$ des-archive-access --help
Usage: des-archive-access [OPTIONS] COMMAND [ARGS]...

  DES archive access CLI. Execute the CLI to start the SQL shell.

Options:
  -l, --loadsql TEXT  Load a SQL command from a file and execute it.
  -c, --command TEXT  Load a SQL command from the command line and execute it.
  --help              Show this message and exit.

Commands:
  sql      Alternative way of loading a sql command from the QUERY...
  sqlrepl  Alternative way of staring the SQL shell.
$ des-archive-access -c "select band, tilename, ccdnum, filename from y6a2_image limit 10;"
found 10 rows in 0.003719 seconds (2688.656410 rows/s)

BAND TILENAME CCDNUM FILENAME
r             17     D00792065_r_c17_r4056p01_bkg.fits
g             40     D00791804_g_c40_r4056p01_bkg.fits
z             43     D00701336_z_c43_r3518p01_bkg.fits
Y             49     D00701878_Y_c49_r3518p01_bkg.fits
Y             3      D00701839_Y_c03_r3518p01_bkg.fits
Y             7      D00702301_Y_c07_r3518p01_bkg.fits
i             14     D00700055_i_c14_r3517p01_immasked.fits
i             44     D00700055_i_c44_r3517p01_immasked.fits
i             15     D00700055_i_c15_r3517p01_immasked.fits
i             62     D00699602_i_c62_r3517p01_bkg.fits
```

If no flag is given, the `des-archive-access` command loads you into SQL shell. You can execute commands against the database via

```bash
$ des-archive-access
> select band, tilename, ccdnum, filename from y6a2_image limit 10; > blah.fits
found 10 rows in 0.015860 seconds (630.504337 rows/s)
> select band, tilename, ccdnum, filename from y6a2_image limit 10;
found 10 rows in 0.000135 seconds (73973.615520 rows/s)

BAND TILENAME CCDNUM FILENAME
r             17     D00792065_r_c17_r4056p01_bkg.fits
g             40     D00791804_g_c40_r4056p01_bkg.fits
z             43     D00701336_z_c43_r3518p01_bkg.fits
Y             49     D00701878_Y_c49_r3518p01_bkg.fits
Y             3      D00701839_Y_c03_r3518p01_bkg.fits
Y             7      D00702301_Y_c07_r3518p01_bkg.fits
i             14     D00700055_i_c14_r3517p01_immasked.fits
i             44     D00700055_i_c44_r3517p01_immasked.fits
i             15     D00700055_i_c15_r3517p01_immasked.fits
i             62     D00699602_i_c62_r3517p01_bkg.fits
> :q
```

`des-archive-access` supports writing query results to disk via the same syntax as `easyaccess`

```bash
$ des-archive-access -c "select band, tilename, ccdnum, filename from y6a2_image limit 10; > blah.fits"
found 10 rows in 0.006988 seconds (1431.014671 rows/s)
$ ls blah.fits
blah.fits
```

This functionality works in both the SQL shell and at the command line.

### Downloading Files from the Archive

You can use the `des-archive-access-download` command to download files from the archive.

```bash
$ des-archive-access-download --help
usage: des-archive-access-download [-h] [-l LIST] [-a ARCHIVE] [-d DESDATA] [-f] [--debug] [file]

Download files from the DES archive at FNAL.

positional arguments:
  file                  file to download

options:
  -h, --help            show this help message and exit
  -l LIST, --list LIST  download all files in a list
  -a ARCHIVE, --archive ARCHIVE
                        HTTPS address of the FNAL archive
  -d DESDATA, --desdata DESDATA
                        The destination DESDATA directory.
  -f, --force           Force the download even if data already exists
  --debug               Print the 'curl' command and stderr to help debug connection and download issues.
$ des-archive-access-download OPS/finalcut/Y6A1/20181129-r4056/D00797980/p01/red/immask/D00797980_r_c27_r4056p01_immasked.fits.fz
/Users/beckermr/DESDATA/OPS/finalcut/Y6A1/20181129-r4056/D00797980/p01/red/immask/D00797980_r_c27_r4056p01_immasked.fits.fz
```

You must set the `DESDATA` environment variable. Files will be downloaded to this location at the same relative path as the location in the archive.

## Differences between `des-archive-access` and `easyaccess`

- `des-archive-access` currently only supports writing SQL queries in FITS binary format and in only a single file.
- All of the `easyaccess` features for introspecting tables and columns are not yet implemented.
