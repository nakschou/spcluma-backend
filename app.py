from flask import Flask, request, Response
from functools import wraps
from lumaai import LumaAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
api_key = os.environ.get("OUR_API_KEY")

def create_custom_response(data, status_code=200, mimetype='application/json'):
    response = Response(
        response=json.dumps(data),
        status=status_code,
        mimetype=mimetype
    )
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.json.get('api_key')
        if not api_key or api_key != os.environ.get("OUR_API_KEY"):       
            return create_custom_response({"error": "Invalid API key"}, 403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/text_to_video', methods=['POST'])
@require_api_key
def text_to_video():
    #get the "text" from the request json
    txt = request.json.get('text')
    start_frame = request.json.get('start_frame')
    if not txt:
        return create_custom_response({'error': 'Missing "text" in request body'}, 400)
    try:
        client = LumaAI(
            auth_token=os.environ.get("LUMAAI_API_KEY"),
        )
        if not start_frame:
            generation = client.generations.create(
                prompt=txt,
            )
        else:
            generation = client.generations.create(
                prompt=txt,
                keyframes={
                "frame0": {
                    "type": "image",
                    "url": start_frame
                }
                }
            )
        id = generation.id
        while generation.state != 'completed':
            generation = client.generations.get(id)
        vid_url = generation.assets.video
        return create_custom_response({'url': vid_url})
    except Exception as e:
        return create_custom_response({'error': str(e)}, 500)

if __name__ == '__main__':
    app.run(debug=True)