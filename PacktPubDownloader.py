#!/usr/bin/python
import requests
import lxml.html
import re

# set login data
email = "superuser@example.com"
password = "supersecretpassword"


# load form data
headers = {'user-agent': 'Mozilla/5.0 (Android; Mobile; rv:13.0) Gecko/13.0 Firefox/13.0'}
r = requests.get('http://www.packtpub.com/', headers=headers)

if r.status_code != 200:
    print("It wasn't possible to load the login form: " + str(r.status_code))
    exit(r.status_code)
# dic to gather login form data
values = {'password': password, 'email': email}
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
    print("It wasn't possible to login in" + str(r.status_code))
    exit(r.status_code)

# extract session toke
js = lxml.html.fromstring(r.content).findall('head/script')
sessionToken = "null"

for j in js:
    m = re.search('"sid":"[A-Za-z0-9]+"', j.text_content())
    if m:
        sessionToken = m.group(0).split('"')[3]
        break

if sessionToken == "null":
    print("The Login doesn't succeed ERROR " + str(r.status_code))
    exit(r.status_code)


# create session cookie
sessionCookie = requests.cookies.RequestsCookieJar()
sessionCookie.set('SESS_live', sessionToken, domain='.packtpub.com', path='/')

# search for free book
r = requests.get('https://www.packtpub.com/packt/offers/free-learning', cookies=sessionCookie, headers=headers)

freebookurl = lxml.html.fromstring(r.content).find_class("twelve-days-claim")[0].get('href')

# request free book for account
r = requests.get('https://www.packtpub.com' + freebookurl, cookies=sessionCookie, headers=headers)

if r.status_code == 200:
    print("Book successfully add to account " + email)
else:
    print("Couldn't collect free book ERROR " + str(r.status_code))
    exit(r.status_code)