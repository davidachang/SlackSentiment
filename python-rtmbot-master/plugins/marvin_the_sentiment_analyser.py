import Algorithmia
import yaml
import traceback
import seaborn as sb
import os
import requests 
import matplotlib.pyplot as plt

import seaborn as sns; sns.set(style="ticks", color_codes=True)
iris = sns.load_dataset("iris")
g = sns.pairplot(iris)
g = sns.pairplot(iris, vars=["sepal_width", "sepal_length"])

g.savefig("SentimentVisuals")

# now let's output the visual file onto the slack channel using the files.upload


curr_path = os.getcwd()

new_path = curr_path + '/SentimentVisuals.png'

print(new_path)

my_file = {
  'file' : (new_path, open(new_path, 'rb'), 'png')
}

payload={
  "filename":"SentimentVisuals.png", 
  "token":"xoxb-460537279170-471500328005-FY5reKb1zGhq3QoMo36IThqY", 
  "channels":['#fuckyouchat'], 
}

r = requests.post("https://slack.com/api/files.upload", params=payload, files=my_file)


# end of the addition


CONFIG = yaml.load(file("rtmbot.conf", "r"))

ALGORITHMIA_CLIENT = Algorithmia.client(CONFIG["ALGORITHMIA_KEY"])
ALGORITHM = ALGORITHMIA_CLIENT.algo('nlp/SocialSentimentAnalysis/0.1.4')

outputs = []

sentiment_results = {
    "negative": 0,
    "neutral": 0,
    "positive": 0
}

sentiment_averages = {
    "negative": 0,
    "neutral": 0,
    "positive": 0,
    "total": 0,
}

def display_current_mood(channel):
    reply = ""

    # something has gone wrong if we don't have a channel do nothing
    if not channel:
        return

    # loop over our stats and send them in the
    # best layout we can.
    for k, v in sentiment_averages.iteritems():
        if k == "total":
            continue
        reply += "{}: {}%\n ".format(k.capitalize(), v)

    outputs.append([channel, str(reply)])
    return

def process_message(data):

    text = data.get("text", None)

    if not text or data.get("subtype", "") == "channel_join":
        return

    # remove any odd encoding
    text = text.encode('utf-8')

    if "current mood?" in text:
        return display_current_mood(data.get("channel", None))

    if "show graph?" in text:
        print(g)

    # don't log the bot replies!
    if data.get("subtype", "") == "bot_message":
        return outputGraphs("channel", None)

    try:
        sentence = {
            "sentence": text
        }

        result = ALGORITHM.pipe(sentence)

        results = result.result[0]

        verdict = "neutral"
        compound_result = results.get('compound', 0)

        if compound_result == 0:
            sentiment_results["neutral"] += 1
        elif compound_result > 0:
            sentiment_results["positive"] += 1
            verdict = "positive"
        elif compound_result < 0:
            sentiment_results["negative"] += 1
            verdict = "negative"

        # increment counter so we can work out averages
        sentiment_averages["total"] += 1

        for k, v in sentiment_results.iteritems():
            if k == "total":
                continue
            if v == 0:
                continue
            sentiment_averages[k] = round(
                float(v) / float(sentiment_averages["total"]) * 100, 2)

        if compound_result < -0.75:
            outputs.append([data["channel"], "Easy there, negative Nancy!"])

        # print to the console what just happened
        print 'Comment "{}" was {}, compound result: {}'.format(text, verdict, compound_result)

    except Exception as exception:
        # a few things can go wrong but the important thing is keep going
        # print the error and then move on
        print "Something went wrong processing the text: {}".format(text)
        print traceback.format_exc(exception)