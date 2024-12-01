from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
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
    result = ''

    image_stream.seek(0)  # Reset stream position
    ocr_result = computervision_client.read_in_stream(image_stream, raw=True)

    operation_location = ocr_result.headers["Operation-Location"] 
    operation_id = operation_location.split("/")[-1]

    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)
    # Display OCR results
    if read_result.status == 'succeeded':
        for page in read_result.analyze_result.read_results:
            for line in page.lines:
                result = result + " " + line.text
    if is_captcha(result):
        return True
    return False
    
def is_captcha(text):
      print(text)
      regex_captcha = r'CAPTCHA|captcha|I\'m not a robot'
      imnotrobot = r'I\'m not a robot'
      if re.search(regex_captcha, text):
            return True
      # use LLM to check CAPTCHA
      prompt = detect_CAPTACH_prompt(text)
      # TODO Limit the use rate of LLM
      if (len(prompt) > 100): prompt = prompt[:300]
      print(prompt)
      llm_output = generate(prompt)
      if re.search(r'true|True', llm_output):
            return True
      return False


def extractTextFromImage(read_image_url):
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