import requests
from bs4 import BeautifulSoup
from googletrans import Translator

url = 'https://www.xyuzhaiwu3.com/read/68723/'
result = requests.get(url)  # get request

if result.status_code == 200:
    content = result.content
    soup = BeautifulSoup(content, "html.parser")
    title_tag = soup.find('h1')

    if title_tag:
        title = title_tag.text.strip()
        print("Original title (Chinese):", title)
        translator = Translator()
        translated_title = translator.translate(title, src='zh-CN', dest='en')
        if translated_title.text:
            print("Translated title (English):", translated_title.text)
            synopsis_div = soup.find('div', id='aboutbook')
            if synopsis_div:
                synopsis_text = synopsis_div.text.strip()
                print("Original Synopsis:")
                print(synopsis_text)
                translated_synopsis = translator.translate(synopsis_text, src='zh-CN', dest='en')
                if translated_synopsis.text:
                    print("\nTranslated Synopsis:")
                    print(translated_synopsis.text)
                else:
                    print("Translation failed.")
            else:
                print("Synopsis not found.")
else:
    print("Failed to fetch the webpage. Status code:", result.status_code)
