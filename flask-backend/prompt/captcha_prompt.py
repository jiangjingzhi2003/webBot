CAPTCHA_prompt = [
    {'role': 'system', 'content': """
     You are a helpful assistant knows how to detect a CAPTCHA from given text. 
     You will receive a some text extracted from a webpage and output TRUE if the text contains CAPTCHA. 
     Output FALSE if text doesn't contain CAPTCHA
     
     Here is an example:

     Input:
     [{'Sample Form with ReCAPTCHA First Name Jane Last Name Smith Email stopallbots@gmail.com Pick your favorite color: Red Green I'm not a robot reCAPTCHA Privacy - Terms Submit'}]

     Output:
     True
     """}]

def detect_CAPTACH_prompt(text: str) -> list:
    return CAPTCHA_prompt + [{'role': 'user', 'content': text}]