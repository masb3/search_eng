# [search_eng](http://toptensearch.herokuapp.com/)

- <b>Overall architecture of the solution:</b>  
Flask on backend to handle request-response for only one route accepting GET/POST. 
Jinja2 is used for html generation from template.  
Since every search request requires calls to Google API, Bing API and to 10 webpages it was decided to use aiohttp to handle asynchroneous network requests.      
Beautifulsoup is used to simplify parsing html pages to fetch custom snippets.  

- <b>Top 10 combined:</b>  
First are the pages returned by both APIs, next by rotation Bing-Google results up to count 10.  

- <b>Challenges:</b>  
Custom snippet generation  
Correct CSS to fullfill requirement: show original snippet if checkbox not checked, otherwise show custom snippet while showing original on snippet hover.    
Problems to obtain Bing API key.  

- <b>Timesheet</b>:  
<i>3h</i> to get Bing API key and make firsat API call.  
<i>2h</i> setup Flask with one route for GET/POST, initial html, async call to Google and Bing, response parse.    
<i>6h</i> choose top 10, fetch custom snippets, prepare for rendering in html, bolding query in custom snippet if matched, getting timestamps, code cleanup.   
<i>2h</i> CSS on frontend.  
<i>1h</i> deployment on Heroku, writing this doc.  

- <b>Demo:</b>  
http://toptensearch.herokuapp.com/
