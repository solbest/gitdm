import pyautogui
import pyperclip
import time
import random
import logging
from rcontents import messages
from rcontents import subjects

def setup_logging(log_file: str):
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
def get_random_subject():
    subject = random.choice(subjects)
    return subject

def get_random_message(name):
    message = random.choice(messages)
    return message.format(name=name)

# Helper to set clipboard content
def set_clipboard(content):
    pyperclip.copy(content)
    time.sleep(0.1)  # slight delay to ensure clipboard is set

def sleepInterval(bRnd = False):
    if(bRnd):
        time.sleep(random.uniform(2, 4.0))
    else:
        time.sleep(0.5)

def send_email(to, subject, content):
    # Send 'c' key
    pyautogui.press('c')
    sleepInterval()

    # First Ctrl+V
    set_clipboard(to)
    pyautogui.hotkey('ctrl', 'v')
    sleepInterval()

    # Tab
    pyautogui.press('tab')
    sleepInterval()

    # Second Ctrl+V
    set_clipboard(subject)
    pyautogui.hotkey('ctrl', 'v')
    sleepInterval()

    # Tab
    pyautogui.press('tab')
    sleepInterval()

    # Third Ctrl+V
    set_clipboard(content)
    pyautogui.hotkey('ctrl', 'v')
    sleepInterval()

    # Tab
    pyautogui.press('tab')
    sleepInterval(True)

    # Enter
    pyautogui.press('enter')

    # Log
    logging.info(f"{recipient}")
    ''

# Load email list with names
with open('emails.txt', 'r', encoding='utf-8') as file:
    email_list = [line.strip().split('\t')[-2:] for line in file if line.strip()]

# 500ms interval 
time.sleep(random.uniform(2, 4.0))  # Give user time to focus the right window
setup_logging("sent_email_list.log")

# Send emails one by one
for name, recipient in email_list:
    send_email(recipient, get_random_subject(), get_random_message(name))