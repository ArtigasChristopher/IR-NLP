# IR-NLP

IR & NLP Repository for the CAU course.

## Content

The objective is to retrieve some data and create a data collection.
Then building an IR System with :

- Boolean Model
- Vector Space Model

For my collection i decided to collect articles talking about AI news by scrapping the venturebeat.com website.

## How to generate Data ?

- By using `python3 Scrap.py` all the articles that can be found on venturebeat.com will be stored in 'articles.json' file.
- You can use `python3 IsolateText.py` to generate txt based on every articles, they will appear inside 'articles_txt' folder.

## How to use IR System ?

- Launching python file with `python3 IRSystem.py` you will have access to the IRSystem console. The different type of request you can ask :
  - 'ai' will search for the word 'ai' with boolean search.
  - 'ai OR openai' will search for one of these words with boolean search.
  - 'ai AND openai' will search for both words in a file with boolean search.
  - 'vector ai' will search for the word 'ai' with vector space search.
