import { isProbablyReaderable, Readability } from '@mozilla/readability';
if (!window.hasInjectedExtractContent) {
  window.hasInjectedExtractContent = true;

  function canBeParsed(document) {
    return isProbablyReaderable(document, {
      minContentLength: 100
    });
  }

  function parse(document) {
    if (!canBeParsed(document)) {
      console.log("can't parse")
      return false;
    }
    const documentClone = document.cloneNode(true);
    const article = new Readability(documentClone).parse();
    return article.textContent;
  }

  const parsedText = parse(window.document);

  if (parsedText){
    chrome.runtime.sendMessage({ action: "parsedContent", data: parsedText });
  }
  // Content script to detect potential CAPTCHA hints on the webpage
  const hasCAPTCHAIndicators = document.body.innerText.match(/I'm not a robot|CAPTCHA|captcha|verify/i);
  // Extract all image URLs from the current page
  const images = document.querySelectorAll("img");
  const imageUrls = Array.from(images).map(img => img.getAttribute("src"));
  // Log the extracted image URLs
  console.log("Extracted Images:", images);

  if (hasCAPTCHAIndicators) {
      // Notify the background script
      chrome.runtime.sendMessage({ detectedCAPTCHA: true , imageUrls, parsedText});
  } else {
      chrome.runtime.sendMessage({ detectedCAPTCHA: false, takeScreenshot: true , imageUrls, parsedText}, (response) => {
          console.log("Screenshot Response:", response);
      });
  }

  console.log("extract_content.js is running for the first time.");
}

parse(window.document);