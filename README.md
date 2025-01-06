# CAPTCHA Detector

This project is a Chrome extension that detects CAPTCHA elements on web pages and uses a Flask backend with Azure Computer Vision API for advanced CAPTCHA analysis.

## **Installation**

### **Chrome Plugin**
1. Clone this repository
2. Run `npm install` in this folder to install all dependencies.
3. Run `npm run build` to build the extension.
4. Navigate to `chrome://extensions`.
5. Enable **Developer Mode**.
6. Load the newly created `dist` directory in Chrome as an [unpacked extension]
7. Click the extension icon to open the summary side panel.
8. Open any web page, the page's content summary will automatically be displayed in the side panel.

### **Flask Backend**
1. Install Python dependencies:
   ```bash
   pip install -r flask-backend/requirements.txt