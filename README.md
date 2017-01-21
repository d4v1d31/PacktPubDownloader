### Packtpub Downloader
This python script claims automatically the [daly free ebook](https://www.packtpub.com/packt/offers/free-learning) on packtpub.com.

#### Install
This script need the lxml and requests libs:
    yum install python-lxml python-requests
Remove the `.example` from the `config.yml` and fill it with your credentials.
The last step is, to make a entry for cron so it runs frequently.

#### todo
- cache session token
- add good cli
- add download progressbar