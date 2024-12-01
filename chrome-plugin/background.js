chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.detectedCAPTCHA) {
        fetch("http://127.0.0.1:5000/detect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ detected: message.detectedCAPTCHA })
        })
        .then(response => response.json())
        .then(data => console.log("CAPTCHA Detection Result:", data))
        .catch(err => console.error("Error:", err));
    }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.takeScreenshot) {
        chrome.tabs.captureVisibleTab(null, { format: "png" }, (dataUrl) => {
            // Send the screenshot data to the backend
            fetch("http://127.0.0.1:5000/detect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ screenshot: dataUrl })
            })
            .then(response => response.json())
            .then(data => {
                console.log("Detection Result:", data);
                sendResponse({ success: true, result: data });
            })
            .catch(err => {
                console.error("Error:", err);
                sendResponse({ success: false, error: err });
            });
        });

        // Required for asynchronous `sendResponse`
        return true;
    }
});