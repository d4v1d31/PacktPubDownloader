#!/usr/bin/python
import requests
import lxml.html
import re
import yaml
import os.path
import urllib2
from tqdm import tqdm

# load config data
cfg = yaml.load(open("config.yml", "r+"))
email = cfg.get('email')
password = cfg.get('password')
session_file = cfg.get('session_token')
book_lib_dir = cfg.get('booklib')
file_type = cfg.get('filetype')  # todo check input

# http header
headers = {'user-agent': 'Mozilla/5.0 (Android; Mobile; rv:13.0) Gecko/13.0 Firefox/13.0'}


# loads login form, logs in and extracts session token
def get_session_id(mail, pw):
    # load form data
    r = requests.get('http://www.packtpub.com/', headers=headers)
    if r.status_code != 200:
        exit_error("It wasn't possible to load the login form", r.status_code)

    # dic to gather login form data
    values = {'password': pw, 'email': mail}
    # grep form
    form = lxml.html.fromstring(r.content).get_element_by_id("packt-user-login-form")

    # get submit field
    submit = form.find('.//input[@name="op"]')

    # get hidden fields
    field1 = form.find('.//input[@name="form_build_id"]')
    field2 = form.find('.//input[@name="form_id"]')

    # dic to gather login form data
    values = {'password': password,
              'email': email,
              'op': submit.value,
              'form_build_id': field1.value,
              'form_id': field2.value}

    # send login request
    r = requests.post('https://www.packtpub.com/', cookies=r.cookies, data=values, headers=headers)

    if r.status_code != 200:
        exit_error("It wasn't possible to login", r.status_code)

    # extract session toke
    js = lxml.html.fromstring(r.content).findall('head/script')
    session_token = "null"

    for j in js:
        m = re.search('"sid":"[A-Za-z0-9]+"', j.text_content())
        if m:
            session_token = m.group(0).split('"')[3]
            break

    if session_token == "null":
        exit_error("The Login doesn't succeed", r.status_code)
    return session_token


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
        print("Book successfully add to account " + email)
    else:
        exit_error("Couldn't collect free book", r.status_code)


# downloads all books in your my books list
def download_all_books(token):
    session_cookie = create_session_cookie(token)
    r = requests.get('https://www.packtpub.com/account/my-ebooks', cookies=session_cookie, headers=headers)
    if r.status_code != 200:
        exit_error("Something went wrong loading your books", r.status_code)

    book_entries = lxml.html.fromstring(r.content).get_element_by_id("product-account-list").find_class("product-line")

    for book in book_entries:
        download_book(book, session_cookie)


# downloads one book
def download_book(book, session_cookie):
    title = str(book.get('title'))
    if title != '':
        print('Downloading: ' + str(book.get('title')))
        url = 'https://www.packtpub.com/ebook_download/' + str(book.get('nid')) + '/' + file_type
        filename = book_lib_dir + '/' + title.replace(' ', '_') + '.' + file_type
        if os.path.isfile(filename):
            print('[skip]')
        else:
            download_file(url, filename, session_cookie)


# downloads a file by url and notifies the progress
def download_file(url, dest, cookies):
    response = requests.get(url, cookies=cookies, headers=headers, stream=True)
    #file = urllib2.urlopen(url, cookies=cookies, headers=headers)
    #with open(dest, 'wb') as output:
    #    output.write(file.read())
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


# simple error handling
def exit_error(msg, err_code):
    print(msg + " [ERROR]:" + str(err_code))
    exit(err_code)


# makes download dir if necessary
def test_lib_dir():
    if not os.path.isdir(book_lib_dir):
        print("Create book lib: " + os.path.abspath(book_lib_dir))
        os.mkdir(book_lib_dir)


test_lib_dir()
# setup session
print('Logging in...')
session_token = get_session_id(email, password)
print('Try to claim the daily free book...')
claim_free_book(session_token)
print('Start downloading all books...')
download_all_books(session_token)
