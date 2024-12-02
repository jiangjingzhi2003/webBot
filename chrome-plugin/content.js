// Content script to detect potential CAPTCHA hints on the webpage
const hasCAPTCHAIndicators = document.body.innerText.match(/I'm not a robot|CAPTCHA|captcha|verify/i);
// Extract all image URLs from the current page
const images = document.querySelectorAll("img");
const imageUrls = Array.from(images).map(img => img.getAttribute("src"));
// Log the extracted image URLs
console.log("Extracted Images:", images);

if (hasCAPTCHAIndicators) {
    // Notify the background script
    chrome.runtime.sendMessage({ detectedCAPTCHA: true , imageUrls});
} else {
    chrome.runtime.sendMessage({ detectedCAPTCHA: false, takeScreenshot: true , imageUrls}, (response) => {
        console.log("Screenshot Response:", response);
    });
}
