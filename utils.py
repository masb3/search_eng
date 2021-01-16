import asyncio
import time

import aiohttp

from bs4 import BeautifulSoup

from config import Config


SNIPPET_FETCH_TIMEOUT_S = 3  # in case some webpage not respond

google_search = 'https://customsearch.googleapis.com/customsearch/v1?key={}&cx={}&num=10'\
    .format(Config.GOOGLE_API, Config.GOOGLE_CX)

bing_search = 'https://api.bing.microsoft.com/v7.0/search/?responseFilter=Webpages&count=10'
bing_header = {'Ocp-Apim-Subscription-Key': Config.BING_API_KEY}


async def async_main_searches(requests):
    async with aiohttp.ClientSession() as session:
        tasks = [async_get_url_json(session, url=req['url'], header=req['header']) for req in requests]
        return await asyncio.gather(*tasks)


async def async_main_snippets(websites):
    async with aiohttp.ClientSession() as session:
        tasks = [async_get_custom_snippet(session, website, websites['query']) for website in websites['searchRes']]
        return await asyncio.gather(*tasks)


async def async_get_url_json(session, url, header):
    ts = time.time()
    async with session.get(url, headers=header) as resp:
        if resp.status == 200:
            resp_json = await resp.json()
            resp_json['reqRespTs'] = time.time() - ts
            return resp_json
        return None


async def async_get_custom_snippet(session, website, query):
    ts = time.time()
    try:
        timeout = aiohttp.ClientTimeout(total=SNIPPET_FETCH_TIMEOUT_S)
        async with session.get(website['url'], timeout=timeout) as resp:
            if resp.status == 200:
                resp_content = await resp.text(encoding='utf-8')  # 'windows-1251, resp.content.read()
                website['customSnippetFetchTs'] = time.time() - ts

                soup = BeautifulSoup(resp_content, 'html.parser')
                meta_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_tag:
                    website['customSnippet'] = meta_tag['content']
                else:
                    website['customSnippet'] = soup.title.string

                # make query bold if found in custom snippet
                try:
                    query_start = website['customSnippet'].lower().index(query.lower())
                    query_end = query_start + len(query) - 1
                    html_snippet = website['customSnippet'][:query_start] + '<b>' + \
                                  website['customSnippet'][query_start:query_end + 1] + '</b>' + \
                                  website['customSnippet'][query_end + 1:]
                    website['customSnippet'] = html_snippet
                except ValueError:
                    pass
                return resp_content
            return None
    except asyncio.exceptions.TimeoutError:
        website['customSnippetFetchTs'] = time.time() - ts
        website['snippetTimeout'] = True
    finally:
        return None


def search_api(query):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Query google and big API search
    google_url = google_search + '&q=%s' % query
    bing_url = bing_search + '&q=%s' % query
    req = [{'url': google_url, 'header': None}, {'url': bing_url, 'header': bing_header}]
    results = loop.run_until_complete(async_main_searches(req))

    # Parse results and combine top 10
    parsed_results = parse_results(results)
    top_ten = get_top_ten(parsed_results)

    top_ten['query'] = query

    # Fetch custom snippets based on webpages info
    loop.run_until_complete(async_main_snippets(top_ten))

    loop.close()
    return top_ten


def parse_results(results):
    parsed_results = {'googleSearchRes': None, 'googleReqRespTs': None, 'bingSearchRes': None, 'bingReqRespTs': None}
    if results[0]:
        parsed_results['googleSearchRes'] = parse_google(results[0])
        parsed_results['googleReqRespTs'] = results[0]['reqRespTs']
    if results[1]:
        parsed_results['bingSearchRes'] = parse_bing(results[1])
        parsed_results['bingReqRespTs'] = results[1]['reqRespTs']
    return parsed_results


def parse_google(result):
    parsed = []
    for item in result['items']:
        parsed.append({'url': item['link'],
                       'title': item['title'],
                       'snippet_orig': item['htmlSnippet'],
                       'engine': 'Google'})
    return parsed


def parse_bing(result):
    parsed = []
    for item in result['webPages']['value']:
        parsed.append({'url': item['url'],
                       'title': item['name'],
                       'snippet_orig': item['snippet'],
                       'engine': 'Bing'})
    return parsed


def get_top_ten(results):
    ret = {'searchRes': None, 'googleReqRespTs': None, 'bingReqRespTs': None}
    if not results['googleSearchRes'] and not results['bingSearchRes']:
        return None
    elif not results['googleSearchRes']:
        ret['searchRes'] = results['bingSearchRes']
        ret['bingReqRespTs'] = results['bingReqRespTs']
        return ret
    elif not results['bingSearchRes']:
        ret['searchRes'] = results['googleSearchRes']
        ret['googleReqRespTs'] = results['googleReqRespTs']
        return ret
    else:
        top_ten = []
        ret['googleReqRespTs'] = results['googleReqRespTs']
        ret['bingReqRespTs'] = results['bingReqRespTs']
        google_res = results['googleSearchRes'].copy()
        bing_res = results['bingSearchRes'].copy()
        for i in range(10):
            if results['googleSearchRes'][i]['url'] == results['bingSearchRes'][i]['url']:
                top_ten.append(results['googleSearchRes'][i])
                del google_res[i]
                del bing_res[i]

        google_now = False
        while len(top_ten) < 10 and google_res and bing_res:
            if google_now:
                google_now ^= True
                top_ten.append(google_res.pop())
            else:
                google_now ^= True
                top_ten.append(bing_res.pop())
        ret['searchRes'] = top_ten
        return ret

