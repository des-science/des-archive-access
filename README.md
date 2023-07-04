# des-archive-access
[![pre-commit](https://github.com/des-science/des-archive-access/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/des-science/des-archive-access/actions/workflows/pre-commit.yml) [![tests](https://github.com/des-science/des-archive-access/actions/workflows/tests.yml/badge.svg)](https://github.com/des-science/des-archive-access/actions/workflows/tests.yml)

tools for accessing the DES data archive at FNAL

## Instructions for Generating a CILogon Certificate

1. Go to [cilogon.org](https://cilogon.org/)
2. Login with your FNAL services account.
3. Click the **Create Password-Protected Certificate** link.
4. Follow the instructions to download a certificate.
5. Use the `des-archive-access-process-cert` command to reformat the certificate for openssl v3. This command will ask you for your password and to set a new password. You can reuse the same password if you'd like. Hopefully we don't have to do this in the future.
6. The password and certificate will be store in the `~/.des_archive_access/` directory in your home area. Make the sure the permissions on this directory are `700` via `chmod 700 ~/.des_archive_access/`.
