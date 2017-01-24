#!/usr/bin/python
import argparse
import os.path
import re

import lxml.html
import requests
import yaml

config_file = "config.yml"

# load config data
if not os.path.isfile(config_file):
    print('No config.yml found: Please set full configuration through params!')
    required = True
    default_filetype = 'pdf'
    default_booklib = 'lib'
    default_sessionfile = '.session'
    default_cache_session = True
    default_email = None
    default_password = None
else:
    required = False
    cfg = yaml.load(open(config_file, "r+"))
    default_filetype = cfg.get('filetype')
    default_booklib = cfg.get('booklib')
    default_email = cfg.get('email')
    default_password = cfg.get('password')
    default_sessionfile = '.session'
    default_cache_session = True

# http header
headers = {'user-agent': 'Mozilla/5.0 (Android; Mobile; rv:13.0) Gecko/13.0 Firefox/13.0'}


# setup cli params
parser = argparse.ArgumentParser(
        description='Packtpub Downloader is a python script to download ebooks from packtpub.com and claim the '
                    'daily free ebook.')
parser.add_argument('-c', '--claim-free-book',
                    dest='claim',
                    action='store_true',
                    help='claims the free book')
parser.add_argument('-d', '--download',
                    action='store_true',
                    help='downloads all books available in my books')
parser.add_argument('-b', '--booklib',
                    default=default_booklib,
                    help='sets the download destination')
parser.add_argument('-p', '--password',
                    required=required,
                    default=default_password,
                    help='sets the password for your packtpub account')
parser.add_argument('-e', '--email',
                    default=default_email,
                    required=required,
                    help='sets the email for your packtpub account')
parser.add_argument("-t", "--file-type", type=str,
                    choices=['pdf', 'epub', 'mobi'],
                    default=default_filetype,
                    help="stets the type to download")
parser.add_argument("-s", "--session-file", type=str,
                    default=default_sessionfile,
                    help="stets the file to cache session token")
parser.add_argument('-C', '--disable-session-cache',
                    dest='cache_session' ,
                    action='store_false',
                    default=default_cache_session,
                    help='disables session caching by file')
args = parser.parse_args()


def send_login_form(mail, pw):
    # load form da
    r = requests.get('http://www.packtpub.com/', headers=headers)
    if r.status_code != 200:
        exit_error("It wasn't possible to load the login form", r.status_code)

    # grep form
    form = lxml.html.fromstring(r.content).get_element_by_id("packt-user-login-form")

    # get submit field
    submit = form.find('.//input[@name="op"]')

    # get hidden fields
    field1 = form.find('.//input[@name="form_build_id"]')
    field2 = form.find('.//input[@name="form_id"]')

    # dic to gather login form data
    values = {'password': pw,
              'email': mail,
              'op': submit.value,
              'form_build_id': field1.value,
              'form_id': field2.value}

    # send login request
    r = requests.post('https://www.packtpub.com/', cookies=r.cookies, data=values, headers=headers)
    if r.status_code != 200:
        exit_error("It wasn't possible to login", r.status_code)

    # extract session token out of js
    token = extract_sess_id(r.content)
    if token == "null":
        exit_error("The Login doesn't succeed", r.status_code)
    return token


def extract_sess_id(site_content):
    # extract session token
    return extract_data('sid', site_content)


def extract_data(attr, site_content):
    js = lxml.html.fromstring(site_content).findall('head/script')
    token = "null"

    for j in js:
        m = re.search('"' + attr + '":"[A-Za-z0-9@.\-_]+"', j.text_content())
        if m:
            token = m.group(0).split('"')[3]
            break
    return token


# loads login form, logs in and extracts session token
def get_session_id(mail, pw):
    # load session token if cached
    if args.cache_session and os.path.isfile(args.session_file):
        # load last session token
        token = read_session()
        # test session token
        session_cookie = create_session_cookie(token)
        r = requests.get('https://www.packtpub.com', cookies=session_cookie, headers=headers)
        # extract session token out of js
        test_mail = extract_data('mail', r.content)
        print(test_mail)
        if test_mail != args.email:
            print("Old token doesn't work.")
            token = send_login_form(mail, pw)
    else:
        # get new session token
        print('Logging in...')
        token = send_login_form(mail, pw)

    # cache token
    if args.cache_session:
        write_session(token)
    return token


# create session cookie
def create_session_cookie(token):
    session_cookie = requests.cookies.RequestsCookieJar()
    session_cookie.set('SESS_live', token, domain='.packtpub.com', path='/')
    return session_cookie


# claims the daily free book
def claim_free_book(token):
    session_cookie = create_session_cookie(token)
    # search for free book
    r = requests.get('https://www.packtpub.com/packt/offers/free-learning', cookies=session_cookie, headers=headers)

    free_book_url = lxml.html.fromstring(r.content).find_class("twelve-days-claim")[0].get('href')

    # request free book for account
    r = requests.get('https://www.packtpub.com' + free_book_url, cookies=session_cookie, headers=headers)

    if r.status_code == 200:
        print("Book successfully add to account " + args.email)
    else:
        exit_error("Couldn't collect free book", r.status_code)


# downloads all books in your my books list
def download_all_books(token):
    session_cookie = create_session_cookie(token)
    r = requests.get('https://www.packtpub.com/account/my-ebooks', cookies=session_cookie, headers=headers)
    if r.status_code != 200:
        exit_error("Something went wrong loading your books", r.status_code)

    book_entries = lxml.html.fromstring(r.content).get_element_by_id("product-account-list").find_class("product-line")
    book_number = len(book_entries) - 1
    i = 0
    for book in book_entries:
        i += 1
        download_book(book, session_cookie, i, book_number)


# downloads one book
def download_book(book, session_cookie, i, n):
    t = book.get('title')
    if t is not None:
        title = str(t.encode('ascii', 'ignore'))  # fix some coding issue
        print('(' + str(i) + '/' + str(n) + ') Downloading: ' + title)
        url = 'https://www.packtpub.com/ebook_download/' + str(book.get('nid')) + '/' + args.file_type

        filename = args.booklib + '/' + title.replace(' ', '_') + '.' + args.file_type
        if os.path.isfile(filename):
            print('[skip]')
        else:
            download_file(url, filename, session_cookie)


# downloads a file by url and notifies the progress
def download_file(url, dest, cookies):
    response = requests.get(url, cookies=cookies, headers=headers, stream=True)
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


# simple error handling
def exit_error(msg, err_code):
    print(msg + " [ERROR]:" + str(err_code))
    exit(err_code)


# makes download dir if necessary
def test_lib_dir(booklib):
    if not os.path.isdir(booklib):
        print("Create book lib: " + os.path.abspath(booklib))
        os.mkdir(booklib)


def read_session():
    sess_file = open(args.session_file, 'r')
    token = sess_file.readline()
    token = token.replace("\n", '')
    return token


def write_session(token):
    sess_file = open(args.session_file, 'w+')
    sess_file.write(token)

# Main program
if args.claim or args.download:
    test_lib_dir(args.booklib)
    session_token = get_session_id(args.email, args.password)
    if args.claim:
        print('Try to claim the daily free book...')
        claim_free_book(session_token)
    if args.download:
        print('Start downloading all books...')
        download_all_books(session_token)
else:
    parser.parse_args(["--help"])
