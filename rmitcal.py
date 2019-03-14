#!/usr/bin/env python
##
## RMIT Timetable to ICS (Calendar Format)
## 
## This tool uses RMIT credentials to authenticate with RMIT and fetch relevant calendar
## data. The data is interpreted into a semesters worth of classes to be imported into  
## applications like Google Calendar and Outlook
##
## Author: Adam Young
##

import requests
from lxml import html
import json
import sys
import random
import re

from datetime import datetime
from datetime import date
from datetime import timedelta

username = sys.argv[1]
password = sys.argv[2]

# Date information no longer needs to be updated every semester
# But the URL relies on whether the year number is even or odd??!?!?
currentYear = datetime.now().year
if currentYear % 2 == 0:
    timetableurl = 'https://mytimetable.rmit.edu.au/even/student'
else:
    timetableurl = 'https://mytimetable.rmit.edu.au/odd/student'

# Important urls
login = 'https://sso-cas.rmit.edu.au/rmitcas/login'

requests.packages.urllib3.disable_warnings()

# Create session with cookies
with requests.session() as c:
    # Grab login token required for post
    tokenrequest = c.get(login)
    tokentree = html.fromstring(tokenrequest.content)

    tokens = tokentree.xpath('//input[@type="hidden"]/@name')
    values = tokentree.xpath('//input[@type="hidden"]/@value')

    # Add credentials to postdata
    payload = {
        'username' : username,
        'password' : password
    }
    # Add additional login tokens
    for i, t in enumerate(tokens):
        payload.update( {t: values[i]} )

    loginrequest = c.post(login, data=payload)

    # Get timetable and parse as  json
    ttreq = c.get(timetableurl)

    # Find data variable and parse
    for line in ttreq.content.splitlines():
        if line.startswith(b'data='):
            timetableJSON = line[5:len(line)-1] # no semi-colon

    student = json.loads( timetableJSON.decode("utf-8") )
    classes = student.get('student').get('allocated')

eventtpl = '''BEGIN:VEVENT
DTEND:{end_ts}
LOCATION:{loc}
DESCRIPTION:{code}
SUMMARY:{type} - {title}
DTSTART:{start_ts}
RRULE:FREQ=WEEKLY;UNTIL={semendstr}
{exl_dt}
END:VEVENT
'''

calendarics = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//hacksw/handcal//NONSGML v1.0//EN
CALSCALE:GREGORIAN
'''

# Loop through each allocated event
for eventstr, event in classes.items():
    
    eventdata = {}

    # Start date is some monday in the past (not start of semester)
    datestr = event.get('start_date')+" "+event.get('start_time')


    # determine number of days after monday this event occurs
    wk_arr = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    wk_day = wk_arr.index(event.get('day_of_week'))

    # week pattern tells us the weeks this event occurs
    #                           v (mid semester break)
    # looks like '0000000001111101111100000000000'
    #                      ^ (start of sem)
    sem_sch = event.get('week_pattern')

    # find start and end of sem
    cstart_wk = sem_sch.find('1');
    cend_wk = sem_sch.rfind('1');

    # determine tijme and date of first class occurence
    start_ts = datetime.strptime(datestr, "%d/%m/%Y %H:%M") + timedelta(days=7*cstart_wk+wk_day)
    # determine length of first class occurence
    end_ts = start_ts + timedelta(seconds=int(event.get('duration'))*60)

    # determine end of semester
    semend = end_ts + timedelta(days=7*(cend_wk-cstart_wk))

    # dates to exclude for this class
    exl_dts = []
    for m in re.finditer('0', sem_sch[cstart_wk:cend_wk]):
        exl_dt = start_ts + timedelta(days=7*m.start())
        exl_dts.append(exl_dt.strftime("%Y%m%dT%H%M%S"))
    if (len(exl_dts) > 0):
        exl_str = "EXDATE;VALUE=DATE:" + ','.join(exl_dts)
    else:
        exl_str = ""


    # Chuck everything into an array
    eventdata.update( {'loc': event.get('location')} )
    eventdata.update( {'code': event.get('subject_code')} )
    eventdata.update( {'type': event.get('activityType')} )
    eventdata.update( {'title': event.get('subject_description')} )
    eventdata.update( {'start_ts': start_ts.strftime("%Y%m%dT%H%M%S")} )
    eventdata.update( {'end_ts': end_ts.strftime("%Y%m%dT%H%M%S")} )
    eventdata.update( {'exl_dt': exl_str} )
    eventdata.update( {'semendstr': semend.strftime("%Y%m%dT%H%M%S")} )

    # Generate VCal string to write to file
    calendarics += eventtpl.format(**eventdata)

calendarics += 'END:VCALENDAR'

calendarfile = 'cal'+username+'.ics'

print(calendarfile)
tt_target = open(calendarfile, 'w')
tt_target.truncate()
tt_target.write(calendarics)
tt_target.close()
