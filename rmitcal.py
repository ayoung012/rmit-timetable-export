#!/usr/bin/env python
##
## RMIT Timetable to ICS (Calendar Format)
## 
## This tool uses RMIT credentials to authenticate with RMIT and fetch relevant calendar
## data. The data is interpreted into a semesters worth of classes to be imported into  
## applications like Google Calendar and Outlook
##
## Author: Adam Young 2016
##

import requests
from lxml import html
import json
import sys
import random

from datetime import datetime
from datetime import date

username = sys.argv[1]
password = sys.argv[2]

# Date information, will need to be updated every semester
year = 2016

startmonth = 7
startday = 18

endmonth = 10
endday = 16

# Important urls
login = 'https://sso-cas.rmit.edu.au/rmitcas/login'
timetableurl = 'https://my.rmit.edu.au/service/myclasstimetable'

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
    #print(loginrequest)

    # Get timetable and parse as  json
    ttreq = c.get(timetableurl)
    timetableJSON = ttreq.content.decode(ttreq.encoding);

    timetable = json.loads( timetableJSON )

    classList = []



# Create the start and end dates for our timetable
#semstart = datetime(year, startmonth, startday)
wkstart = date.fromtimestamp( int(timetable['weekStartDate']/1000) )
semend = datetime(year, endmonth, endday)


eventtpl = '''BEGIN:VEVENT
DTEND:{end_ts}
LOCATION:{loc}
GEO:{lat};{long}
DESCRIPTION:{code}
SUMMARY:{type} - {title}
DTSTART:{start_ts}
RRULE:FREQ=WEEKLY;UNTIL={semendstr}
END:VEVENT
'''

calendarics = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//hacksw/handcal//NONSGML v1.0//EN
CALSCALE:GREGORIAN
'''

for day in timetable.get( 'weeklyTimetable' ):
    for classinfo in day.get( 'dailyTimetable' ):
        
        eventdata = {}

        # Convert the display time into seconds from midnight
        # This must be done as the actual startTime timestamp given
        # in JSON response is just midnight for every class
        start_sfm = int( (datetime.strptime(classinfo.get('startDisplayable'), "%I.%M %p") - datetime(1900,1,1)).total_seconds() )
        end_sfm = int( (datetime.strptime(classinfo.get('endDisplayable'), "%I.%M %p") - datetime(1900,1,1)).total_seconds() )

        # convert into seconds from epoch
        start_ts = datetime.fromtimestamp( int(classinfo.get('startTime')/1000) + start_sfm ) 
        end_ts = datetime.fromtimestamp( int(classinfo.get('endTime')/1000) + end_sfm )

        # Chuck everything into an array
        eventdata.update( {'loc': classinfo.get('location')} )
        eventdata.update( {'lat': classinfo.get('latitude')} )
        eventdata.update( {'long': classinfo.get('longitude')} )
        eventdata.update( {'code': classinfo.get('subject') + classinfo.get('catalogNumber')} )
        eventdata.update( {'type': classinfo.get('activityType')} )
        eventdata.update( {'title': classinfo.get('title')} )
        eventdata.update( {'start_ts': start_ts.strftime("%Y%m%dT%H%M%S")} )
        eventdata.update( {'end_ts': end_ts.strftime("%Y%m%dT%H%M%S")} )
        eventdata.update( {'semendstr': semend.strftime("%Y%m%dT%H%M%S")} )

        calendarics += eventtpl.format(**eventdata)

calendarics += 'END:VCALENDAR'

calendarfile = 'cal'+username+'.ics'

print(calendarfile)
tt_target = open(calendarfile, 'w')
tt_target.truncate()
tt_target.write(calendarics)
tt_target.close()
