import json

with open('credentials/maiko-ai/picovoice.json', 'r') as f:
    credentials = json.load(f)
    accessKey = credentials['ACCESS_KEY']



print(accessKey)