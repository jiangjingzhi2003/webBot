from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from msrest.authentication import CognitiveServicesCredentials
import os
import time
from dotenv import load_dotenv
from selenium import webdriver
import io
import re
from typing import List, Dict, Any, Callable
from openai import AzureOpenAI
from prompt.captcha_prompt import detect_CAPTACH_prompt
from prompt.summary_prompt import summary_prompt

load_dotenv()

subscription_key = os.environ["VISION_KEY"]
endpoint = os.environ["VISION_ENDPOINT"]
location = os.environ["VISION_LOCATION"]
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

#
# takes website url and determin if the website contain CAPTCHA#
def detectCAPTCHA(imageData):
    image_stream = imageData
    analysis = computervision_client.analyze_image_in_stream(image_stream, visual_features=["Objects", "Tags", "Description"])
    # print(f'computer vision analysis of current tab {analysis}')
    result = ''

    image_stream.seek(0)  # Reset stream position
    ocr_result = computervision_client.read_in_stream(image_stream, raw=True)

    operation_location = ocr_result.headers["Operation-Location"] 
    operation_id = operation_location.split("/")[-1]
	
    """while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)
    # Display OCR results
    if read_result.status == 'succeeded':
        for page in read_result.analyze_result.read_results:
            for line in page.lines:
                result = result + " " + line.text"""
    if is_captcha(result):
        return True
    return False
    
# function takes in text extracted from a screenshot of a website and check if the website contain keywords
def is_captcha(text):
      regex_captcha = r'CAPTCHA|captcha|I\'m not a robot'
      imnotrobot = r'I\'m not a robot'
      if re.search(regex_captcha, text):
            return True
      # use LLM to check CAPTCHA
      prompt = detect_CAPTACH_prompt(text)
      # TODO Limit the use rate of LLM
      if (len(prompt) > 100): prompt = prompt[:300]
      # llm_output = generate(prompt)
      # if re.search(r'true|True', llm_output):
            # return True
      return False

def extractTextFromImage(read_image_url):
	read_response  = computervision_client.read(read_image_url ,  raw=True)

	result = ''
	# Get the operation location (URL with an ID at the end) from the response
	read_operation_location = read_response.headers["Operation-Location"]
	# Grab the ID from the URL
	operation_id = read_operation_location.split("/")[-1]
	
	# Call the "GET" API and wait for it to retrieve the results 
	while True:
		read_result = computervision_client.get_read_result(operation_id)
		if read_result.status not in ['notStarted', 'running']:
			break
		time.sleep(1)

	# Add the detected text to result, line by line
	if read_result.status == OperationStatusCodes.succeeded:
		for text_result in read_result.analyze_result.read_results:
			for line in text_result.lines:
				result = result + " " + line.text
	return result

def generate(prompt: List[Dict[str, str]], temperature: float = 0.7, top_p: float = 0.95) -> str:
    """
    Send a prompt to an API endpoint of an LLM and retrieve a response.

    Args:
        prompt (List[Dict[str, str]]): A list of message dictionaries representing the conversation history.
        temperature (float, optional): The sampling temperature for the model's output. Defaults to 0.7.
        top_p (float, optional): The cumulative probability cutoff for top-p sampling. Defaults to 0.95.

    Returns:
        str: The content of the response message from the API.
    """
    client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],  
    api_version="2024-08-01-preview",
    azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    )
    response = client.chat.completions.create(
    model='gpt-4',    
    messages= prompt)
    return response.choices[0].message.content

# classify all images extracted from the web
def classifyMultiImages(imageURLs):
	for img in imageURLs:
		classifyImage(img)

# classify a single image using image url
def classifyImage(read_image_url):
	read_response  = computervision_client.read(read_image_url ,  raw=True)
	print(read_response)

	result = ''
	# Get the operation location (URL with an ID at the end) from the response
	read_operation_location = read_response.headers["Operation-Location"]
	# Grab the ID from the URL
	operation_id = read_operation_location.split("/")[-1]
	
	# Call the "GET" API and wait for it to retrieve the results 
	while True:
		read_result = computervision_client.get_read_result(operation_id)
		if read_result.status not in ['notStarted', 'running']:
			break
		time.sleep(1)

	# Add the detected text to result, line by line
	if read_result.status == OperationStatusCodes.succeeded:
		for text_result in read_result.analyze_result.read_results:
			for line in text_result.lines:
				result = result + " " + line.text
	return result

def summarizer(text, config):
	"""
	summarize the input text with matching configuration
	
	Args:
        text(str): web content to summerize
		config(dict): {"type",
		                "length",
						"format"}
	Return 
        str: summerized text
	"""
	from azure.core.credentials import AzureKeyCredential
	from azure.ai.textanalytics import (
        TextAnalyticsClient,
        ExtractiveSummaryAction
    ) 
	key = os.environ['LANGUAGE_KEY']
	endpoint = os.environ['LANGUAGE_ENDPOINT']
	ta_credential = AzureKeyCredential(key)
	text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, 
            credential=ta_credential)
	processed_text = [text]
	type = config['type']
	# determine the length to produce summary
	length = config['length']
	if length == 'short': sentence_count = 1
	elif length == 'medium': sentence_count = 3
	else: sentence_count = 5
	
	poller = text_analytics_client.begin_analyze_actions(
        processed_text,
        actions=[
            ExtractiveSummaryAction(max_sentence_count=sentence_count)
        ],
    )
	document_results = poller.result()
	output_summaries = []
	for result in document_results:
		output_summary = "Summary extracted: \n{}"
		extract_summary_result = result[0]  # first document, first result
		print(extract_summary_result)
		if extract_summary_result.is_error:
			print("...Is an error with code '{}' and message '{}'".format(
                extract_summary_result.code, extract_summary_result.message
            ))
		else:
			output_summary = formatter(extract_summary_result.sentences, type)
		output_summaries.append(output_summary)
	return output_summaries[0]
	
def formatter(sentences, type):
	if type == 'key-points':
		output_summary = keypoint_formater(sentences)
	else:
		output_summary = "Summary extracted: \n{}".format(" ".join([sentence.text for sentence in sentences])) 
	return output_summary

def keypoint_formater(sentences):
	final_output = "Summary extracted: \n"
	for sentence in sentences:
		format_sentence = f"- {sentence.text} \n"
		final_output += format_sentence
	return final_output
		
#based on https://github.com/mihranmiroyan/edison.git
def embed_text(text: str, model_name: str) -> List[float]:
    """
    Generate an embedding for a given text using a specified model via Azure OpenAI.

    Args:
        text (str): The input text to generate the embedding for.
        model_name (str): The name of the model to use for generating the embedding.

    Returns:
        List[float]: A list representing the embedding vector for the input text.
    """
    client = AzureOpenAI(
        api_key=os.environ["EMBEDDING_KEY"],  
        api_version="2023-05-15",
        azure_endpoint=os.environ["EMBEDDING_ENDPOINT"]
    )
    response = client.embeddings.create(input=text, model="text-embedding-ada-002")
    return response.data[0].embedding
	
def split_text(text, sentences_per_chunk = 5):
    # Split the text into sentences using a regex
    sentences = re.findall(r'[^.!?]+[.!?]+', text)
    if not sentences:
        print("No sentences found in the text.")
        return []

    # Group sentences into chunks
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = ' '.join(sentences[i:i + sentences_per_chunk]).strip()
        chunks.append(chunk)

    return chunks
    

	
