from flask import Flask, request, jsonify, render_template
import requests
from util import extractTextFromImage, detectCAPTCHA, summarizer, split_text
from rag import chat_with_web, create_index_from_text
import io, base64
from PIL import Image


app = Flask(__name__)

@app.route("/home", methods=['GET'])
def ai():
    return render_template("index.html")

@app.route("/detect", methods=["POST"])
def detect_captcha():
    print('start captcha detection')
    data = request.get_json()

    images = data.get('imageURL', [])  # List of image URLs or Base64 strings
    textContent = data.get('textContent')
    if not images:
        return jsonify({'error': 'No images provided'}), 400
    
    screenshot = data.get("screenshot")
    if ('detected' in data) and data['detected'] :
        return jsonify({"double_checked": False, "contains_captcha": True})
    
    if screenshot:
        # Decode the Base64 image
        image_data = base64.b64decode(screenshot.split(",")[1])
        image_stream = io.BytesIO(image_data)
        image = Image.open(io.BytesIO(image_data))
        
        # Save the image for debugging (optional)
        image.save("screenshot_for_double_check.png")

        contains_captcha = detectCAPTCHA(image_stream)
        
        return jsonify({"double_checked": True, "contains_captcha": contains_captcha})
    
    return jsonify({"contains_captcha": False})

@app.route("/summary", methods=["POST"])
def summarize():
    data = request.get_json()
    print(data['config']['length'])
    textContent = data.get('textContent')
    configuration = data.get('config')
    length = configuration['length']
    summary_content = summarizer(textContent, configuration)
    if summary_content:
        return jsonify({"summary_success":True, "summary_content":summary_content})
    return jsonify({"summary_success":False, "summary_content":summary_content})

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    textContent = data.get('textContent')
    query = data.get('query')
    chunks = split_text(textContent)
    index_name = create_index_from_text("newyorktimeindex", chunks)
    chat_repsonse = chat_with_web(query, index_name, 1)['message']
    if chat_repsonse:
        return jsonify({"success":True, "answer":chat_repsonse})
    return jsonify({"success":False, "answer":chat_repsonse})


if __name__ == "__main__":
    app.run(debug=True)
