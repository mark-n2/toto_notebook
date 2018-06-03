import requests
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print('Encountered a start tag:', tag)
    def handle_endtag(self, tag):
        print('Encountered an end tag :', tag)
    def handle_data(self, data):
        print('Encountered some data :', data)

year = 2018
competition = 1

url = 'https://data.j-league.or.jp/SFMS01/search?competition_years='+ str(year) + '&competition_frame_ids=' + str(competition)

print(url)
res = requests.get(url)
res.raise_for_status()

parser = MyHTMLParser()
parser.feed(res.text)