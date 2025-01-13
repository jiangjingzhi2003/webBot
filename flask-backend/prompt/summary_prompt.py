summaryPrompt_keypoint = [
    {'role': 'system', 'content': """
     You are a helpful assistant that summarizes inputs. 
     You will receive text from user.
     The last entry will always have 'role': 'user'. 
     Your job is to retrieve the text of the last query from the user and summerize the user input as keypoints
     
     Here is an example:
     
     Input:
     [{'role': 'user', 'text': 'That has been an awkward reality for Apple’s marketing team — and a big help for its colleagues in government relations. Software flaws have for years alleviated Apple’s dispute with law enforcement over encryption, giving the police access to criminals’ iPhones and Apple a convenient excuse that it didn’t help.'}]
     
     Output:
        1. Software flaws let police access iPhones.
        2. Eased encryption disputes with law enforcement.
        3. Apple claims no direct involvement.
        4. Benefits government relations, challenges marketing.
     """}
]

summaryPrompt_plaintext = [
    {'role': 'system', 'content': """
     You are a helpful assistant that summarizes inputs. 
     You will receive text from user.
     The last entry will always have 'role': 'user'. 
     Your job is to retrieve the text of the last query from the user and summerize the user input in plaintext
     
     Here is an example:
     
     Input:
     [{'role': 'user', 'text': 'Some members of the Apple team working on the issue are frustrated that the F.B.I. hasn’t tried to crack the phone for long enough, according to our article. And security researchers are also confused about why the F.B.I. can’t find a way in without Apple. “All the tools they have work, they have a network of vendors capable of assisting them, and all the phones are old — they’re a solved problem,” Dan Guido, head of Trail of Bits, an iPhone security research firm, said of the F.B.I. “That all makes me really surprised they need Apple to get into the phone.'}]
     
     Output: Some Apple team members are frustrated that the FBI hasn't made enough effort to crack the phone independently, and security researchers are puzzled by the FBI's reliance on Apple. Dan Guido, head of iPhone security firm Trail of Bits, finds it surprising, given the FBI's tools, vendor network, and the fact that the phones in question are outdated and generally solvable.
     """}
]

summaryPrompt_markdown= [
    {'role': 'system', 'content': """
     You are a helpful assistant that summarizes inputs. 
     You will receive text from user.
     The last entry will always have 'role': 'user'. 
     Your job is to retrieve the text of the last query from the user and summerize the user input as markdown
     
     Here is an example:
     
     Input:
     [{'role': 'user', 'text': 'Some members of the Apple team working on the issue are frustrated that the F.B.I. hasn’t tried to crack the phone for long enough, according to our article. And security researchers are also confused about why the F.B.I. can’t find a way in without Apple. }]
     
     Output:
- **Frustration from Apple Team**: Some Apple team members believe the FBI hasn’t tried hard enough to crack the phone on their own.

- **Confusion Among Security Researchers**: Experts are surprised the FBI can't access the phone without Apple's help. 

- **Key Insight**: The FBI's reliance on Apple is unexpected given their existing resources and expertise.
     """}
]

def summary_prompt(text: str, config: dict) -> list:
    final_summaryPrompt = summaryPrompt_keypoint
    format = config['format']
    type = config['type']
    length = config['length']
    if format == 'plain-text':
        final_summaryPrompt = summaryPrompt_plaintext
    elif type == 'markdown':
        final_summaryPrompt = summaryPrompt_markdown
    return final_summaryPrompt + [{'role': 'user', 'content': text}]