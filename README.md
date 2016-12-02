# rmit-timetable-export
A calender export script written specifically for RMIT in Python.
Takes RMIT credentials and fetches class data to be interpreted into an ICS file.
Outputs to a file named calsXXXXXXX.ics (where XX... is the given student number)

Usage: python rmitcal.py \<username> \<password>

Test on Python 2.6.6 and runs on Python 3 AFAIK

Requires these two Python packages:
Requests 2.12.3
https://pypi.python.org/pypi/requests/
lxml 3.4.4
http://lxml.de/installation.html
