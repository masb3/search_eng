import time

from flask import Flask, render_template, request

from utils import search_api


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        ts = time.time()
        ret = search_api(request.form['query'])
        if ret['searchRes']:
            return render_template('index.html',
                                   query=ret['query'],
                                   items=ret['searchRes'],
                                   google_ts=ret['googleReqRespTs'],
                                   bing_ts=ret['bingReqRespTs'],
                                   total_time=time.time()-ts)

    resp = render_template('index.html')
    return resp
