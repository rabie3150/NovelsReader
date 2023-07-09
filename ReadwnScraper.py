import json
import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urlencode
import re


class ReadwnScraper:
    def __init__(self, sourceId, baseUrl , sourceName, options={}):
        self.sourceId = sourceId
        self.sourceName = sourceName
        self.baseUrl = baseUrl
        self.path = options.get('path', {
            'novels': 'novel',
            'novel': 'novel',
            'chapter': 'novel'
        })        
        self.scraper= 'ReadwnScraper'
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',})
        self.session = session

    def popularNovels(self, output_file=None):
		# return a list of novels in the main page still needs som world to devide into popular / new / ...
        url = self.baseUrl
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        novels = []

        for novel in soup.select('.novel-item'):
            novel_name = novel.select_one('h4').text.strip()
            novel_Full_url = self.baseUrl + novel.select_one('a')['href']
            novel_url = novel.select_one('a')['href'].strip().replace(self.path['novel'], '').replace('/','').replace('.html', '')
            cover_url = novel.select_one('img')['data-src'].strip()
            novel_cover = self.baseUrl + cover_url

            novels.append({
				'sourceId': self.sourceId,
                'novelName': novel_name,
                'novelCover': novel_cover,
                'novelUrl': novel_url,
                'novelFullUrl': novel_Full_url
            })

        if output_file:
            with open(output_file, 'w') as file:
                json.dump(novels, file)
        return novels

    def parseNovelAndChapters(self, novelUrl, output_file=None):
        FullnovelUrl = f"{self.baseUrl}{self.path['novel']}/{novelUrl}.html"

        response = self.session.get(FullnovelUrl)
        soup = BeautifulSoup(response.text, 'html.parser')

        novel_name = soup.select_one('h1.novel-title').text.strip()
        cover_url = soup.select_one('figure.cover > img')['data-src'].strip()
        novel_cover = self.baseUrl + cover_url
        summary = soup.select_one('.summary').text.strip().replace('Summary', '')
        genre = ', '.join([item.text.strip() for item in soup.select('div.categories > ul > li')])
        status = soup.select_one('div.header-stats > span:-soup-contains("Status") strong').text.strip()
        author = soup.select_one('span[itemprop="author"]').text.strip()

        last_chapter_no = 1
        latest_chapter_no = int(soup.select_one('.header-stats span > strong').text.strip())
        chapter_list = soup.select('.chapter-list li')

        novel_details = {
            'novelName': novel_name,
            'novelCover': novel_cover,
            'summary': summary,
            'genre': genre,
            'status': status,
            'author': author,
            'chaptersCount' : len(chapter_list),
            'chapters': []
        }


        for chapter in chapter_list:
            chapter_name = chapter.select_one('a .chapter-title').text.strip()
            chapterUrl = chapter.select_one('a')['href'].strip().replace(self.path['novel'], '').replace('/','')
            release_date = chapter.select_one('a .chapter-update').text.strip()
            chapter_no_text = chapter.select_one('a .chapter-no').text.strip()

            novel_details['chapters'].append({
                'chapterName': chapter_name,
                'chapterUrl': chapterUrl,
                'releaseDate': release_date,
                'chapterNumber': chapter_no_text
            })

        # Add missing chapters (if any)
        last_chapter_no += 1
        for i in range(last_chapter_no, latest_chapter_no + 1):
            chapter_name = f'Chapter {i}'
            chapter_url = f'{novelUrl}_{i}.html'
            release_date = None

            novel_details['chapters'].append({
                'chapterName': chapter_name,
                'chapterUrl': chapter_url,
                'releaseDate': release_date
            })


        if output_file:
            with open(output_file, 'w') as file:
                json.dump(novel_details, file)

        return novel_details

    def parseChapter(self, novelUrl, chapterUrl, output_file=None):        
        retry_count=0
        max_retries=10
        
        url = f"{self.baseUrl}{self.path['novel']}/{chapterUrl}"

        response = self.session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_name = soup.select_one('.book-chapter h2').text.strip() if soup.select_one('.book-chapter h2') else "Chapter Name Not Found"

        # Check if chapter text is found
        chapter_text_element = soup.select_one('div.chapter-content')
        if chapter_text_element:
            chapter_text = chapter_text_element.get_text('\n').strip()
        else:
            if retry_count >= max_retries:
                self.logger.error(f'Skipping chapter {chapterUrl} - Maximum retry count reached for novel {self.novel_id}')
                return None

            time.sleep(2)  # Wait for 2 seconds
            return self.scrape_chapter(chapterUrl, retry_count=retry_count+1, max_retries=max_retries)  # Retry scraping the chapter

        chapter = {
            'sourceId': self.sourceId,
            'novelUrl': novelUrl,
            'chapterUrl': chapterUrl,
            'chapterName': chapter_name,
            'chapterText': chapter_text
        }

        return chapter

    def searchNovels(self, searchTerm):
        baseUrl = self.baseUrl
        sourceId = self.sourceId
        searchUrl = f"{baseUrl}e/search/index.php"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f"{baseUrl}search.html",
            'Origin': baseUrl,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
        }

        data = {
            'show': 'title',
            'tempid': 1,
            'tbname': 'news',
            'keyboard': searchTerm,
        }

        response = requests.post(searchUrl, headers=headers, data=urlencode(data))
        body = response.text

        soup = BeautifulSoup(body, 'html.parser')

        novels = []

        for novel_item in soup.select('li.novel-item'):
            novel_name = novel_item.find('h4').text
            novel_Full_url = self.baseUrl + novel_item.find('a')['href']
            novel_url = novel_item.find('a')['href'].replace(self.path['novel'], '').replace('/','').replace('.html', '')
            chapters_count_str = novel_item.select_one('div.novel-stats span:-soup-contains("Chapters")')
            try :
                chapters_count = int(chapters_count_str.text.split()[0])
            except :
                try :
                    chapter_text = chapters_count_str.text
                    chapters_count = int(re.search(r'\d+', chapter_text).group())
                except:
                    chapters_count = 0
            cover_url = novel_item.find('img')['data-src']
            novel_cover = baseUrl + cover_url

            novel = {
                'sourceId': sourceId,
                'novelName': novel_name,
                'novelCover': novel_cover,
                'novelUrl': novel_url,
                'novelFullUrl': novel_Full_url,
                'chaptersCount' : chapters_count
            }

            novels.append(novel)

        return novels



def main() :
    sourceId=1
    baseUrl='https://www.novelmt.com/'
    sourceName= 'novelmt'
    # chapterurl = 'entertainment-exploration-playing-zhang-qilin-reba-posted-upside-down_002'
    # novelurl= 'immortal-emperor-reborn-in-the-mixed-city'

    source = ReadwnScraper( sourceId, baseUrl,sourceName)
    popularNovels = source.popularNovels()

    for novel in popularNovels :
        print(novel['novelName'])
    
    novel = popularNovels[1]
    novelUrl = novel['novelUrl']
    noveldetails = source.parseNovelAndChapters(novelUrl)
    novelchapters = noveldetails['chapters']
    novelchapter = novelchapters[1]
    chapterUrl = novelchapter['chapterUrl']
    
    chapter = source.parseChapter(novelUrl, chapterUrl)
    chapter_text = chapter['chapterText']
    
    print(chapter_text)
    



    # novels = source.searchNovels('world')
    # for novel in novels :
    #     print(novel['novelName'])
        


if __name__=='__main__':
    main()
