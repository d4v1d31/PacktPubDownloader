### Packtpub Downloader
This python script claims automatically the [daly free ebook](https://www.packtpub.com/packt/offers/free-learning) on packtpub.com.

#### Install
This script need the lxml and requests libs:
    yum install python-lxml python-requests
Remove the `.example` from the `config.yml` and fill it with your credentials.
The last step is, to make a entry for cron so it runs frequently.

#### Usage
    usage: PacktPubDownloader.py [-h] [-c] [-d] [-b BOOKLIB] [-p PASSWORD]
                             [-e EMAIL] [-t {pdf,epub,mobi}]

    Packtpub Downloader is a python script to download ebooks from packtpub.com
    and claim the daily free ebook.
    
    optional arguments:
      -h, --help            show this help message and exit
      -c, --claim-free-book
                            claims the free book
      -d, --download        downloads all books available in my books
      -b BOOKLIB, --booklib BOOKLIB
                            sets the download destination
      -p PASSWORD, --password PASSWORD
                            sets the password for your packtpub account
      -e EMAIL, --email EMAIL
                            sets the email for your packtpub account
      -t {pdf,epub,mobi}, --file-type {pdf,epub,mobi}
                            stets the type to download
