import re
import sys
import concurrent.futures
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from googletrans import Translator

sys.stdout.reconfigure(encoding='utf-8')  # set encoding due to the website is in Chinese


def scrap_content(url):
    result = requests.get(url)  # get request
    content = result.text  # extract the content
    soup = BeautifulSoup(content, "html.parser")
    href_links_set = {re.search(r'/read/(\d+)/', a['href']).group(1) for a in soup.find_all('a', href=True) if
                      '/read' in a['href']}  # store all the numbers in the href links
    return href_links_set


def scrape_novels(urls):  # function to scrape the novels
    href_links_set = set()  # store the href links
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:  # use concurrent to run together
        future_to_url = {executor.submit(scrap_content, url): url for url in urls}  # submit the url to the executor
        for future in concurrent.futures.as_completed(future_to_url):  # check if the future is completed
            url = future_to_url[future]  # get the url
            try:
                data = future.result()  # get the result
                href_links_set.update(data)  # update the set
            except Exception as exc:  # if there is an exception
                print(f"Scraping failed for URL {url}: {exc}")
    return href_links_set


def fetch_page_content(url):  # function to fetch the page content
    result = requests.get(url)  # get request
    return result.content, url  # return the content and the url


def process_page_content(args):
    content, url = args
    soup = BeautifulSoup(content, "html.parser")
    title_tag = soup.find('h1')
    synopsis_tag = soup.find('div', id='aboutbook')
    if title_tag and synopsis_tag:
        title = title_tag.text.strip()
        synopsis = synopsis_tag.text.strip()
        return title, synopsis, url
    return None, None, None


def main():
    start_time = time.time()  # start the timer
    urls = [f"https://[website_hidden].com/sort8/{page}/" for page in range(1, 650)]
    existing_urls = set()  # set for existing URLs
    try:
        existing_novels = pd.read_csv('Novel.csv')  # read the existing novels
        existing_urls = set(existing_novels['Link'])  # extract existing URLs
    except FileNotFoundError:
        print("Novel.csv file not found. Creating a new one.")

    new_links = scrape_novels(urls)  # scrape the new urls

    new_novels = []  # store the new novels
    if new_links:
        translator = Translator()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            page_contents = executor.map(fetch_page_content,
                                         [f"https://www.[website_hidden].com/read/{link}/" for link in new_links])
            for result in executor.map(process_page_content, page_contents):
                if result:
                    title, synopsis, url = result
                    if url in existing_urls:
                        print(f"Skipping {url}")
                        continue
                    time.sleep(1)
                    if title:
                        try:
                            translated_result = translator.translate(title, src='zh-cn', dest='en')
                            translated_title = translated_result.text
                        except Exception as e:
                            print(f"Error translating title: {title}")
                            print(e)
                            continue
                    if synopsis:
                        try:
                            translated_synopsis = translator.translate(synopsis, src='zh-cn', dest='en')
                            translated_synopsis_text = translated_synopsis.text
                        except Exception as e:
                            print(f"Error translating synopsis for title: {title}")
                            print(e)
                            continue
                    words_to_search = ['words_hidden']
                    pattern = r'\b(?:' + '|'.join(words_to_search) + r')\b'
                    if re.search(pattern, translated_title, flags=re.IGNORECASE) is None:
                        new_novels.append((translated_title, translated_synopsis_text, url))

    else:
        print("No new URLs found.")
    if new_novels:
        new_novels_url = set()  # set for new novels
        try:
            new_novels_df = pd.read_excel('new_novels.xlsx')   # read the new novels
            new_novels_url = set(new_novels_df['URL'])
        except FileNotFoundError:
            print("new_novels.xlsx file not found. Creating a new one.")

        new_novels_data = []  # store the new novels data
        for title, synopsis, url in new_novels:
            if url in new_novels_url: # if the url is in the set
                print(f"Skipping {title}")
                continue
            new_novels_data.append({'Title': title, 'Synopsis': synopsis, 'URL': url})

        new_novels_df = pd.DataFrame(new_novels_data) # create a DataFrame

        excel_filename = 'new_novels.xlsx'  # Name of the Excel file
        new_novels_df.to_excel(excel_filename, index=False) # Write the DataFrame to an Excel file

        print(f"New novels information has been written to '{excel_filename}'.") # print the message

    end_time = time.time()  # end the timer
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")  # print the execution time
    total_novels_added = len(new_novels_data)
    print(f"{total_novels_added} new novels added to '{excel_filename}'.")


if __name__ == '__main__':  # run the main function
    main()
