import DOMPurify from 'dompurify';
import { marked } from 'marked';
// The underlying model has a context of 1,024 tokens, out of which 26 are used by the internal prompt,
// leaving about 998 tokens for the input text. Each token corresponds, roughly, to about 4 characters, so 4,000
// is used as a limit to warn the user the content might be too long to summarize.
const MAX_MODEL_CHARS = 4000;

let pageContent = '';

const summaryElement = document.body.querySelector('#summary');
const warningElement = document.body.querySelector('#warning');
const summaryTypeSelect = document.querySelector('#type');
const summaryFormatSelect = document.querySelector('#format');
const summaryLengthSelect = document.querySelector('#length');

function onConfigChange() {
  const oldContent = pageContent;
  pageContent = '';
  onContentChange(oldContent);
}

[summaryTypeSelect, summaryFormatSelect, summaryLengthSelect].forEach((e) =>
  e.addEventListener('change', onConfigChange)
);

//get page content from temporary storage in Chrome browser
chrome.storage.session.get('pageContent', ({ pageContent }) => {
  console.log('current page content is ' + pageContent);
  onContentChange(pageContent);
});

chrome.storage.session.onChanged.addListener((changes) => {
  const pageContent = changes['pageContent'];
  console.log('current page content is ' + pageContent);
  onContentChange(pageContent.newValue);
});

function onContentChange(newContent) {
  if (pageContent == newContent) {
    // no new content, do nothing
    return;
  }
  console.log("Detected webpage, sending to backend..." + newContent);
  console.log("display content"+ newContent);
  fetch("https://llmbackend-d2huf9hubpg5bfht.westus-01.azurewebsites.net/summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({textContent:newContent})
  })
  .then(response => response.json())
  .then(data => {
      console.log("summary:", data);
      showSummary(data.summary_content)
  })
  .catch(err => console.error("Error in summary:", err));
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