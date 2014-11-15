import datetime
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

def get():
    soup = BeautifulSoup(requests.get("http://www.bom.gov.au/nsw/observations/sydney.shtml").text)

    stations = defaultdict(dict)
    for ii in soup.table.tbody.find_all('tr'):
        for kk in ii.find_all('td', {'headers': ['obs-temp', 'obs-relhum', 'obs-datetime']}):
            try:
                vtype = kk['headers'][0].split('-')[1]
                if vtype == 'datetime':
                    value = datetime.datetime.combine(datetime.datetime.today() \
                                                              .replace(day=int(kk.text[:kk.text.find('/')])),
                                                      datetime.datetime.strptime(kk.text[kk.text.find('/') + 1:], '%I:%M%p').time())
                else:
                    value = float(kk.text)
                stations['_'.join(kk['headers'][1].split('-')[2:])][vtype] = value
            except ValueError:
                pass

    return stations


if __name__ == '__main__':
    print get()
