import DOMPurify from 'dompurify';
import { marked } from 'marked';
// The underlying model has a context of 1,024 tokens, out of which 26 are used by the internal prompt,
// leaving about 998 tokens for the input text. Each token corresponds, roughly, to about 4 characters, so 4,000
// is used as a limit to warn the user the content might be too long to summarize.
const MAX_MODEL_CHARS = 125000;

let pageContent = '';
let currentMode = 'summarizer'; // Track the current mode

const summaryElement = document.body.querySelector('#summary');
const warningElement = document.body.querySelector('#warning');
const summaryTypeSelect = document.querySelector('#type');
const summaryFormatSelect = document.querySelector('#format');
const summaryLengthSelect = document.querySelector('#length');
const toggleModeButton = document.querySelector('#toggle-mode');
const resultsCard = document.getElementById("results-card");
const resultsContent = document.getElementById("results-content");
const summarizeButton = document.getElementById("summarize-btn");
const queryButton = document.getElementById("query-btn");
const queryInput = document.getElementById("query-input");

const api_endpoint_summary = 'https://llmbackend-d2huf9hubpg5bfht.westus-01.azurewebsites.net/summary'
const api_endpoint = 'http://127.0.0.1:5000'

// Toggle between Summarizer and Query modes
toggleModeButton.addEventListener('click', () => {
  currentMode = currentMode === 'summarizer' ? 'query' : 'summarizer';
  document.querySelector('#panel-title').textContent =
    currentMode === 'summarizer' ? 'Summarizer' : 'Query';
  toggleModeButton.textContent =
    currentMode === 'summarizer' ? 'Switch to Query Mode' : 'Switch to Summarizer Mode';

  // Show/Hide respective panels
  document.querySelector('#summarizer-panel').hidden = currentMode !== 'summarizer';
  document.querySelector('#query-panel').hidden = currentMode !== 'query';

  // Clear results on mode change
  summaryElement.innerHTML = '';
  warningElement.setAttribute('hidden', '');
});


const config_default = {
  type: summaryTypeSelect.value,
  format: summaryFormatSelect.value,
  length: summaryLengthSelect.value,
  content: '',
};

async function onConfigChange() {
  const oldContent = pageContent;

  const configData = {
    type: summaryTypeSelect.value,
    format: summaryFormatSelect.value,
    length: summaryLengthSelect.value,
    content: oldContent,
  };
  console.log('change configuration ' + configData['length'])
  pageContent = '';
  showSummary('Loading...')
  await sleep(5000) //wait 5 sec before regenerate summary
  onContentChange(oldContent, configData); //update summary content
}

[summaryTypeSelect, summaryFormatSelect, summaryLengthSelect].forEach((e) =>
  e.addEventListener('change', onConfigChange)
);

//get page content from temporary storage in Chrome browser
chrome.storage.session.get('pageContent', ({ pageContent:storedContent }) => {
  pageContent = storedContent || ''; 
  console.log('page content right after fetch from storage ' + pageContent)
  showSummary('Loading...')
  if (currentMode === 'summerizer'){
    onContentChange(pageContent);
  }
});

chrome.storage.session.onChanged.addListener((changes) => {
  const pageContent = changes['pageContent'];
  console.log('page content changed, the current page content is ' + pageContent.newValue);
  if (currentMode === 'summerizer'){
    showSummary('Loading...')
    onContentChange(pageContent);
  }
});

// Handle summarizer functionality
summarizeButton.addEventListener("click", () => {
  onConfigChange()
});

queryButton.addEventListener("click", () => {
  const query = queryInput.value.trim();
  if (!query) {
    resultsCard.hidden = false;
    resultsContent.textContent = "Please enter a query.";
    return;
  }

  resultsCard.hidden = false;
  queryContent(pageContent, query);
});


async function onContentChange(newContent, config=config_default) {
  if (pageContent == newContent) {
    // no new content, do nothing
    console.log('same content and same config, no call for summary')
    return;
  }
  pageContent = newContent
  let summary = ''
  if (newContent) {
    if (newContent.length > MAX_MODEL_CHARS) {
      updateWarning(
        `Text is too long for summarization with ${newContent.length} characters (maximum supported content length is ~1000 characters).`
      );
    } else {
      updateWarning('');
    }
    summary = await generateSummary(newContent, config)
  } else {
    summary = "There's nothing to summarize";
  }
  showSummary(summary)
}

async function generateSummary(newContent, config){
  console.log("Detected webpage, sending to backend...");
  console.log("Current config: ", config);
  try {
    const response = await fetch(api_endpoint + "/summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ textContent: newContent, config: config }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Summary:", data);

    // Assuming the summary is in `data.summary_content`
    return data.summary_content;
  } catch (err) {
    console.error("Error in summary:", err);
    throw err; // Rethrow the error so the caller can handle it
  }
}

//display summary content
async function showSummary(text) {
  summaryElement.innerHTML = DOMPurify.sanitize(marked.parse(text));
}

async function updateWarning(warning) {
  warningElement.textContent = warning;
  if (warning) {
    warningElement.removeAttribute('hidden');
  } else {
    warningElement.setAttribute('hidden', '');
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Query website content
async function queryContent(content, query) {
  console.log('Querying content...');
  try {
    const response = await fetch(api_endpoint + "/query", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ textContent: content, query: query }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    console.log('data response is' + data['answer'])
    showAnswer(data['answer'])
    return data['answer'];
  } catch (err) {
    console.error('Error in query:', err);
    return 'Error querying content.';
  }
}

async function showAnswer(text) {
  resultsContent.innerHTML = DOMPurify.sanitize(marked.parse(text));
}

