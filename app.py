from flask import Flask, request, Response
from functools import wraps
from lumaai import LumaAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
api_key = os.environ.get("OUR_API_KEY")

dct = {
    "hawaii": "https://storage.cdn-luma.com/lit_lite_inference_v1.6-xl/8c60fedd-e5dd-4ff9-a73b-75656951d393/9e638e85-ce84-4f3f-8b2a-5ef5b20e3955_video02646ea6f897542689b259f573b3f0b31.mp4",
    "hongkong": "https://storage.cdn-luma.com/lit_lite_inference_v1.6-xl/b4be73bd-48b1-483b-b5c1-9f70768da411/8318dded-9dba-435d-aefa-2604f69815f5_video0ff773ea00fdd4435988ed76e770bf912.mp4",
    "boston": "https://storage.cdn-luma.com/lit_lite_inference_v1.6-xl/3e19cf0b-942d-4d34-beae-bdfe3ace48f6/edf5bd5b-66ce-4fa1-aca1-ba85c8895af9_video0ae9e4655296944319cb6776ea66c564b.mp4",
    "colorado": "https://storage.cdn-luma.com/lit_lite_inference_v1.6-xl/7be059ea-1d7c-4ba3-af1c-c61783625a17/3fee2fa7-5dde-4fa5-ad72-cd829fd656ad_video0aff89037c13341aa93ae73c76d686248.mp4"
}

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

@app.route('/filter_videos', methods=['POST'])
def filter_videos():
    #get the "text" from the request json
    txt = request.json.get('location')
    if not txt or txt not in dct:
        return create_custom_response({'error': 'Invalid text'}, 400)
    else:
        return create_custom_response({'url': dct[txt]})

if __name__ == '__main__':
    app.run(debug=True)