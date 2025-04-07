#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: frontend.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-04-06 22:05:22
# Modified: 2025-04-06 23:30:11

from flask import Flask, render_template, request, Response, stream_with_context
from echoai.interactor import Interactor
from echoai.tools.get_weather import get_weather
from queue import Queue, Empty
import threading
import time
import os

app = Flask(__name__, static_folder="static", template_folder="templates")

# Init Interactor with tools and streaming
interactor = Interactor(model="openai:gpt-4o-mini", stream=True, tools=True)
interactor.add_function(get_weather)

@app.route("/")
def index():
    return render_template("index.html")
    #return render_template("echoai.html")

@app.route("/stream", methods=["POST"])
def stream():
    user_input = request.form.get("message", "")

    def event_stream():
        q = Queue()

        def stream_callback(token):
            q.put(token)

        def generate_response():
            try:
                interactor.interact(user_input, output_callback=stream_callback, stream=True, tools=True)
            finally:
                q.put(None)

        threading.Thread(target=generate_response, daemon=True).start()

        while True:
            try:
                token = q.get(timeout=0.25)
                if token is None:
                    break
                yield token
            except Empty:
                continue

    return Response(stream_with_context(event_stream()), content_type="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, threaded=True, port=port)

