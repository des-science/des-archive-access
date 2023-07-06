# des-archive-access

[![pre-commit](https://github.com/des-science/des-archive-access/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/des-science/des-archive-access/actions/workflows/pre-commit.yml) [![tests](https://github.com/des-science/des-archive-access/actions/workflows/tests.yml/badge.svg)](https://github.com/des-science/des-archive-access/actions/workflows/tests.yml)

tools for accessing the DES data archive at FNAL

## Instructions for Generating a CILogon Certificate (2023/07/05)

In order to download files from thr archive, you need a CILogon certificate. Follow the instructions below to obtain one.

1. Go to [cilogon.org](https://cilogon.org/)
2. Login with your FNAL services account.
3. Click the ***Create Password-Protected Certificate*** link.
4. Follow the instructions to download a certificate.
5. Reformat the certificate by executing `des-archive-access-process-cert /path/to/cert`. This command will ask you for your password and to set a new password. You can reuse the same password if you'd like or set no password. Hopefully we don't have to do this in the future.

The certificate will be stored in the `~/.des_archive_access/` directory in your home area. **Make the sure the permissions on this directory are `700` via `chmod 700 ~/.des_archive_access/`.** You can change this location by setting the environment variable `DES_ARCHIVE_ACCESS_DIR`.

You need to export the certificate password via the DES_ARCHIVE_ACCESS_PASSWORD (which you can add to your `~/.bashrc` or similar):

```bash
export DES_ARCHIVE_ACCESS_PASSWORD=yourpassword
```

## Usage

### Downloading the Archive Metadata

Before you can query the file archive metadata, you need to download the metadata database (roughly 30GB!!!) via the `des-archive-access-download-metadata`
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
> sql select band, tilename, ccdnum, filename from y6a2_image limit 10; > blah.fits
found 10 rows in 0.015860 seconds (630.504337 rows/s)
> sql select band, tilename, ccdnum, filename from y6a2_image limit 10;
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
usage: des-archive-access-download [-h] [-l LIST] [-a ARCHIVE] [-d DESDATA] [-f] [file]

download files from the DES archive at FNAL

positional arguments:
  file                  file to download

options:
  -h, --help            show this help message and exit
  -l LIST, --list LIST  download all files in a list
  -a ARCHIVE, --archive ARCHIVE
                        HTTPS address of the FNAL archive
  -d DESDATA, --desdata DESDATA
                        The destination DESDATA directory.
  -f, --force           force the download even if data already exists
$ des-archive-access-download OPS/finalcut/Y6A1/20181129-r4056/D00797980/p01/red/immask/D00797980_r_c27_r4056p01_immasked.fits.fz
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100 14.1M  100 14.1M    0     0  13.6M      0  0:00:01  0:00:01 --:--:-- 15.3M
/Users/beckermr/DESDATA/OPS/finalcut/Y6A1/20181129-r4056/D00797980/p01/red/immask/D00797980_r_c27_r4056p01_immasked.fits.fz
```

You must set the `DESDATA` environment variable. Files will be downloaded to this location at the same relative path as the location in the archive.

## Differences between `des-archive-access` and `easyaccess`

- `des-archive-access` currently only supports writing SQL queries in FITS binary format and in only a single file.
- When executing SQL commands in the SQL shell, you have to prefix the command by `sql`.
- All of the `easyaccess` features for introspecting tables and columns are not yet implemented.
