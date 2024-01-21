import requests

def send_notification(
    email_data={}):

    url = "https://api.postmarkapp.com/email"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Postmark-Server-Token': '3064a316-c492-499f-b418-c10ff91df1f7'
    }

    data = {
        "From": "domenico.martynski@trify.pl",
        "To": "domenico.martynski@trify.pl",
        "Subject": email_data['title'],
        "Tag": "string",
        "HtmlBody": email_data['body'],
        "TextBody": email_data['body'],
        "ReplyTo": "domenico.martynski@trify.pl",
        "TrackOpens": True,
        "TrackLinks": "None",
        #"Headers": [
        #    {
        #        "Name": "string",
        #        "Value": "string"
        #    }
        #],
        #"Attachments": [
        #   {
        #      "Name": "string",
        #     "Content": "string",
        #    "ContentType": "string",
        #   "ContentID": "string"
        # }
        #]
    }

    response = requests.post(url, json=data, headers=headers)

