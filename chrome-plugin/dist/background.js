chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.tabs.onActivated.addListener((activeInfo) => {
    showSummary(activeInfo.tabId);
});
chrome.tabs.onUpdated.addListener(async (tabId) => {
    showSummary(tabId);
});

async function showSummary(tabId) {
    const tab = await chrome.tabs.get(tabId);
    if (!tab.url.startsWith('http')) {
        return;
    }
    const injection = await chrome.scripting.executeScript({
        target: { tabId },
        files: ['scripts/content.js']
    });
    console.log("output from content.js " + injection[0].result)
    chrome.storage.session.set({ pageContent: injection[0].result});
}

chrome.runtime.onMessage.addListener( (message, sender, sendResponse) => {
    console.log(message)
    if (!message.imageUrls) {
        console.log("no image in the website");
    }
    // Handle CAPTCHA detection message
    if (message.detectedCAPTCHA) {
        console.log("Detected CAPTCHA, sending to backend...");
        fetch("https://llmbackend-d2huf9hubpg5bfht.westus-01.azurewebsites.net/detect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ detected: message.detectedCAPTCHA, imageURL:message.imageUrls, textContent:message.parsedContent})
        })
        .then(response => response.json())
        .then(data => {
            console.log("CAPTCHA Detection Result:", data);
            sendResponse({ success: true, result: data }); // Optional if you need a response back
        })
        .catch(err => console.error("Error in CAPTCHA detection fetch:", err));
        
        return true; // Ensure asynchronous response handling
    }

    // Handle screenshot request message
    if (message.takeScreenshot) {
        console.log("Taking screenshot for further analysis...");
        const screenshotUrl = chrome.tabs.captureVisibleTab();
        console.log("Try to take a screeshot",  screenshotUrl);

        chrome.tabs.captureVisibleTab(null, { format: "png" }, (dataUrl) => {
            if (!dataUrl) {
                console.error("Failed to capture screenshot.");
                sendResponse({ success: false, error: "Failed to capture screenshot" });
                return;
            }

            console.log("Screenshot captured, sending to backend...");
            fetch("https://llmbackend-d2huf9hubpg5bfht.westus-01.azurewebsites.net/detect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ screenshot: dataUrl, imageURL:message.imageUrls})
            })
            .then(response => response.json())
            .then(data => {
                console.log("Screenshot Detection Result:", data);
                sendResponse({ success: true, result: data });
            })
            .catch(err => {
                console.error("Error in screenshot detection fetch:", err);
                sendResponse({ success: false, error: err.message });
            });
        });
        return true; // Ensure asynchronous response handling
    }
});
