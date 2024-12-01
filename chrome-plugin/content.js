// Content script to detect potential CAPTCHA hints on the webpage
const hasCAPTCHAIndicators = document.body.innerText.match(/I'm not a robot|CAPTCHA|captcha|verify/i);

if (hasCAPTCHAIndicators) {
    // Notify the background script
    chrome.runtime.sendMessage({ detectedCAPTCHA: true });
} else {
    chrome.runtime.sendMessage({ detectedCAPTCHA: false });
    chrome.runtime.sendMessage({ takeScreenshot: true }, (response) => {
        console.log("Screenshot Response:", response);
    });
}