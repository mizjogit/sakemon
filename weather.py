import requests
from bs4 import BeautifulSoup
from collections import defaultdict

def get():
    soup = BeautifulSoup(requests.get("http://www.bom.gov.au/nsw/observations/sydney.shtml").text)

    stations = defaultdict(dict)
    for ii in soup.table.tbody.find_all('tr'):
        for kk in ii.find_all('td', {'headers': ['obs-temp', 'obs-relhum']}):
            try:
                stations['_'.join(kk['headers'][1].split('-')[2:])][kk['headers'][0].split('-')[1]] = float(kk.text)
            except ValueError:
                pass

    return stations


if __name__ == '__main__':
    print get()
