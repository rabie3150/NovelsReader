import requests
from bs4 import BeautifulSoup
import datetime
import json
import cloudscraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re


class MadaraScraper:
    def __init__(self, sourceId, baseUrl, sourceName, options={}):
        self.sourceId = sourceId
        self.baseUrl = baseUrl
        self.sourceName = sourceName
        self.path = options.get('path', {
            'novels': 'novel',
            'novel': 'novel',
            'chapter': 'novel'
        })
        self.scraper= 'MadaraScraper'
        self.useNewChapterEndpoint = options.get('useNewChapterEndpoint', False)

    def popularNovels(self, page=1, show_latest_novels=False, output_file=None):
        sort_order = '?m_orderby=latest' if show_latest_novels else '/?m_orderby=views'
        url = f"{self.baseUrl}/{self.path['novels']}/page/{page}{sort_order}"

        # Use cloudscraper to fetch the page content and bypass Cloudflare
        scraper = cloudscraper.create_scraper()

        try:
            response = scraper.get(url)
        except cloudscraper.exceptions.CloudflareChallengeError:
            attempts = 2
            for i in range(attempts):
                try:
                    if i > 0:
                        time.sleep(2)  # Wait 2 seconds between attempts
                    response = scraper.get(url)
                    if response.status_code != 403:
                        break
                except Exception as e:
                    print(f"Error occurred during attempt {i+1}: {str(e)}")
            else:
                # If all attempts failed, switch to using Selenium
                options = Options()
                options.add_argument("--user-data-dir=/path/to/chrome/profile")  # Path to Chrome user profile
                driver = webdriver.Chrome(options=options)

                try:
                    driver.get(url)

                    # Let the user solve the captcha manually in the browser
                    input("Please solve the captcha in the opened Chrome browser. Press Enter when done.")

                    # Get the page source after the captcha is solved
                    page_content = driver.page_source
                finally:
                    driver.quit()
        else:
            # If the response status code is not 403, then Cloudflare protection is likely bypassed using cloudscraper
            page_content = response.text

        soup = BeautifulSoup(page_content, 'html.parser')

        novels = []

        manga_titles = soup.select('.manga-title-badges')
        for manga_title in manga_titles:
            manga_title.extract()

        page_item_details = soup.select('.page-item-detail')
        for page_item_detail in page_item_details:
            novel_name = page_item_detail.select_one('.post-title').text.strip()
            image = page_item_detail.select_one('img')
            novel_cover = image.get('data-src') or image.get('src')
            novel_Full_url = page_item_detail.select_one('.post-title a')['href']
            novel_url = novel_Full_url.split('/')[4]

            novel = {
                'sourceId': self.sourceId,
                'novelName': novel_name,
                'novelCover': novel_cover,
                'novelUrl': novel_url,
                'novelFullUrl': novel_Full_url
            }

            novels.append(novel)

        if output_file:
            with open(output_file, 'w') as file:
                json.dump(novels, file)

        return {'novels': novels}

    def parseNovelAndChapters(self, novelUrl, output_file=None):
        url = f"{self.baseUrl}/{self.path['novel']}/{novelUrl}/"

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        novel = {}

        novel['sourceId'] = self.sourceId
        novel['sourceName'] = self.sourceName
        novel['url'] = url
        novel['novelUrl'] = novelUrl
        novel['novelFullUrl'] = url
        manga_titles = soup.select('.manga-title-badges')
        for manga_title in manga_titles:
            manga_title.extract()

        novel['novelName'] = soup.select_one('.post-title h1').text.strip()

        summary_image = soup.select_one('.summary_image > a > img')
        novel['novelCover'] = summary_image.get('data-src') or summary_image.get('src')

        post_content_items = soup.select('.post-content_item')
        for post_content_item in post_content_items:
            detail_name = post_content_item.select_one('h5').text.strip()
            detail = post_content_item.select_one('.summary-content').text.strip()

            if detail_name in ['Genre(s)', 'التصنيفات']:
                novel['genre'] = detail.replace('\t', '').replace('\n', ',')
            elif detail_name in ['Author(s)', 'المؤلف']:
                novel['author'] = detail
            elif detail_name in ['Status', 'الحالة']:
                if 'OnGoing' in detail or 'مستمرة' in detail:
                    novel['status'] = 'ONGOING'
                else:
                    novel['status'] = 'COMPLETED'

        novel_summary = soup.select_one('div.summary__content')
        novel['summary'] = novel_summary.text.strip().replace('\n', '')

        novel_chapters = []

        if not self.useNewChapterEndpoint:
            rating_post_id = soup.select_one('.rating-post-id')
            manga_chapters_holder = soup.select_one('#manga-chapters-holder')
            novel_id = rating_post_id.get('value') or manga_chapters_holder.get('data-id')

            formData = {
                'action': 'manga_get_chapters',
                'manga': novel_id
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(f"{self.baseUrl}/wp-admin/admin-ajax.php", data=formData, headers=headers)
            html = response.text
        else:
            response = requests.post(f"{url}ajax/chapters/")
            html = response.text

        loadedCheerio = BeautifulSoup(html, 'html.parser')

        wp_manga_chapters = loadedCheerio.select('.wp-manga-chapter')
        for wp_manga_chapter in wp_manga_chapters:
            chapter_name = wp_manga_chapter.select_one('a').text.strip()


            chapterUrl = wp_manga_chapter.select_one('a')['href'].split('/')
            if len(chapterUrl) > 6:
                chapterUrl = f"{chapterUrl[5]}/{chapterUrl[6]}"
            else:
                chapterUrl = chapterUrl[5]

            chapter = {
                'chapterName': chapter_name,
                'chapterUrl': chapterUrl
            }

            novel_chapters.append(chapter)

        novel['chapters'] = novel_chapters[::-1]

        novel['chaptersCount'] = len(novel_chapters)

        if output_file:
            with open(output_file, 'w') as file:
                json.dump(novel, file)
        return novel

    def parseChapter(self, novelUrl, chapterUrl, output_file=None):
        sourceId = self.sourceId

        url = f"{self.baseUrl}/{self.path['chapter']}/{novelUrl}/{chapterUrl}"

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        if sourceId == 130:
            fonts = soup.select('font')
            for font in fonts:
                font.extract()

        chapter_name_element = soup.select_one('.text-center') or soup.select_one('#chapter-heading')
        if chapter_name_element:
            chapter_name = chapter_name_element.text.strip()
        else:
            chapter_name = "Chapter Name Not Found"

        chapter_text_element = (
            soup.select_one('.text-left') or
            soup.select_one('.text-right') or
            soup.select_one('.entry-content') or 
            soup.select_one('.entry-content_wrap')
        )
        if chapter_text_element:
            chapter_text = chapter_text_element.get_text(separator='\n').strip()
        else:
            chapter_text = "Chapter Text Not Found"

        chapter_text = re.sub('\n+', '\n', chapter_text)
        chapter = {
            'sourceId': sourceId,
            'novelUrl': novelUrl,
            'chapterUrl': chapterUrl,
            'chapterName': chapter_name,
            'chapterText': chapter_text
        }
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(chapter_text)
            # print(f"Chapter saved to {output_file}.")

        return chapter

    def searchNovels(self, searchTerm):
        url = f"{self.baseUrl}/?s={searchTerm}&post_type=wp-manga"
        sourceId = self.sourceId

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        novels = []

        c_tabs_item_contents = soup.select('.c-tabs-item__content')
        for c_tabs_item_content in c_tabs_item_contents:
            novel_name = c_tabs_item_content.select_one('.post-title').text.strip()

            image = c_tabs_item_content.select_one('img')
            novel_cover = image.get('data-src') or image.get('src')
            novel_Full_url = c_tabs_item_content.select_one('.post-title a')['href']
            novel_url = novel_Full_url.split('/')[4]
            latest_chapter_number = c_tabs_item_content.select_one('.latest-chap .chapter').text.strip()
            chapter_number = int(re.findall(r'\d+', latest_chapter_number)[0])
            novel = {
                'sourceId': sourceId,
                'novelName': novel_name,
                'novelCover': novel_cover,
                'novelUrl': novel_url,
                'novelFullUrl': novel_Full_url,
                'chaptersCount' : chapter_number
            }

            novels.append(novel)

        return novels




# def main():
#     check_for_updated_chapters()



# # def main() :

# #     file_path = r"C:\Users\rabie\Desktop\scraper\Madara\MadaraSources.json"
# #     selected_source = get_source(file_path)

# #     # Access the selected source's properties
# #     sourceId = selected_source['sourceId']
# #     baseUrl = selected_source['baseUrl']
# #     sourceName = selected_source['sourceName']
# #     options = selected_source['options']



# #     print(f"Selected source: {sourceName} (ID: {sourceId})")
# #     print(f"Base URL: {baseUrl}")
# #     print(f"Options: {options}")

# #     # Create an instance of MadaraScraper
# #     madara_scraper = MadaraScraper(sourceId, baseUrl, sourceName,options)

# #     # # Parse novel details and chapters and save to 'novel_details.json'
# #     # novel=madara_scraper.parseNovelAndChapters('beauty-and-the-beasts')
    
# #     # Parse a chapter and save to 'chapter.json'
# #     chapter_data = madara_scraper.parseChapter('beauty-and-the-beasts', 'chapter-1660')
# #     print(chapter_data)

# if __name__=='__main__':
#     main()