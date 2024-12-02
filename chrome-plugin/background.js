chrome.runtime.onMessage.addListener( (message, sender, sendResponse) => {
    if (message.imageUrls) {
        console.log("Images extracted from the page:", message.imageUrls);
        // Optionally, process the images here
    }
    
    // Handle CAPTCHA detection message
    if (message.detectedCAPTCHA) {
        console.log("Detected CAPTCHA, sending to backend...");
        fetch("http://127.0.0.1:5000/detect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ detected: message.detectedCAPTCHA, imageURL:message.imageUrls})
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
            fetch("http://127.0.0.1:5000/detect", {
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
