from flask import Flask, request, jsonify
import requests
from util import extractTextFromImage, detectCAPTCHA
import io, base64
from PIL import Image


app = Flask(__name__)

@app.route("/detect", methods=["POST"])
def detect_captcha():
    print('start captcha detection')
    data = request.get_json()
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

if __name__ == "__main__":
    app.run(debug=True)
