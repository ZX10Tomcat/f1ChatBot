from ergast_API import url_to_soup

def latest_news_details():

    articles = []

    homepage = "https://www.formula1.com/"

    soup = url_to_soup(homepage)

    featured_article = soup.find('a', class_="article-teaser-featured-link ")
    this_article = {}
    this_article['title'] = featured_article.find('h4').text
    this_article['date'] = featured_article.find('p', class_='teaser-date').text.strip()
    this_article['article_url'] = homepage[:-1] + featured_article['href']
    this_article['article_image'] = homepage[:-1] + featured_article.find('figure')['data-crop']

    articles.append(this_article)

    for article in soup.find_all('a', class_="article-teaser-link ")[:5]:
        this_article = {}
        this_article['title'] = article.find('h4').text
        this_article['date'] = article.find('p', class_='teaser-date').text.strip()
        this_article['article_url'] = homepage[:-1] + article['href']
        this_article['article_image'] = homepage[:-1] + article.find('figure')['style'].split('(')[1][:-1]
        articles.append(this_article)

    return articles

def latest_videos_details():

    videos = []

    homepage = "https://www.formula1.com/en/video.html"
    source = "https://www.formula1.com/"

    soup = url_to_soup(homepage)

    for video in soup.find('div', class_='articles').find_all('div', class_="video-teaser  column column-4 standard")[:6]:
        this_video = {}
        this_video['title'] = video.find('div', class_='details').h4.text
        this_video['date'] = video.find('div', class_='details').p.text.strip()
        this_video['article_url'] = source[:-1] + video.a['href']
        this_video['article_image'] = source[:-1] + video.find('figure')['style'].split('(')[1][1:-2]
        videos.append(this_video)

    return videos

def latest_news_to_generic(news_or_videos = 'news'):
    elements = []

    if news_or_videos == 'news':
        articles = latest_news_details()
    else:
        articles = latest_videos_details()

    for article in articles:
        element = {}
        element['title'] = article['title']
        element['image_url'] = article['article_image']
        element['subtitle'] = article['date']

        element['default_action'] = {"type": "web_url",
                                      "url": article['article_url'],
                                      "messenger_extensions": True,
                                      "webview_height_ratio": "tall",
                                      "fallback_url": article['article_url']
                                      }

        if news_or_videos == 'news':
            element['buttons'] = [{
                                "type":"web_url",
                                "url" : article['article_url'],
                                "title":"Read article"
                                },
                                {
                                "type":"element_share"
                                }]
        else:
            element['buttons'] = [{
                                "type":"web_url",
                                "url" : article['article_url'],
                                "title":"Watch video"
                                },
                                {
                                "type":"element_share"
                                }]

        elements.append(element)
    return elements

def flags_to_generic():
    homepage = "https://www.formula1.com/en/championship/inside-f1/understanding-f1-racing/Flags.html"
    source = "https://www.formula1.com/"

    soup = url_to_soup(homepage)

    elements = []
    element = {}
    element['title'] = "Flags"
    element['image_url'] = source[:-1] + soup.find('picture', class_ = 'parallax actual').find('img')['src']
    element['subtitle'] = "Understanding F1 racing"

    element['default_action'] = {"type": "web_url",
                                  "url": homepage,
                                  "messenger_extensions": True,
                                  "webview_height_ratio": "tall",
                                  "fallback_url": homepage
                                  }

    element['buttons'] = [{
                        "type":"web_url",
                        "url" : homepage,
                        "title":"Read more"
                        },
                        {
                        "type":"element_share"
                        }]

    elements.append(element)
    return elements

def tickets_button_list():
    url = "https://tickets.formula1.com/"
    buttons_list = [('web_url', 'Buy Tickets', url)]
    return buttons_list
