# Assignment 2: 3 Services Implemented

Service #1 - API calls for NHL Team Information (Simple). Included as a tool. tools_sports.py
This is a very simple service. It pulls the data from the API and parses out the structured data for the model to use.
The service returns basic information about the NHL team including the roster, the amount of forwards, defencemen and goalies. It may add
some insight to the team. The LLM determines what it adds - but follows the instructions in prompt.py

Service #2 - Simple Semantic Query search, via topic, of BBC News Articles.  You search via a topic, and it will search the dataset 
to see if articles for that topic exist. Used ChromaDB persistent and API Embeddings. Generates Chroma DB once. This tool is tools_bbcnews.py
The file is in the repo and is loaded only the first time. bbc_news.csv is broken down into type, categorey, content and embeddings are then stored
in the chromaDB. We use cosine similarity.

Service #3 - Simple Web search used Duck Duck Go. Had to get help with a parser to parse through the data. Did not use the Duck Duck Go Library. This tool is tools_websearch.py. For example if you ask what the capital is of a country it will return data. it is a very simple search. You can 
make it better if you use the DDG library.

To be transparent: I am still learning python. I used the class concepts - but I needed help with the Python code. However I incorporated concepts
learned in class. API calls, ChromaDB/Embeddings, Duck Duck GO Search etc.

## Services

I used the same format as the example. Services stated above. This implementation is based on LangGraph's tools. 

The file main.py contains the llm model calls that controls the chat. Tools are in the files tools_*.py.

## User Interface

+ used what was in the sample
+ It is using the LLM to execute (LangChain etc)
+ Added conversational style.
+ Implemented in Gradio
+ See workflow of user interface below
+ User message
     ↓
    call_model  →  LLM reads tool descriptions → decides which tool fits
     ↓
    tools_condition  →  tool call detected?
     ↓ yes
    ToolNode  →  runs the function, returns result
     ↓
    call_model  →  LLM reads result, writes final answer
     ↓
    User sees response

---

## Guardrails and Other Limitations - These were all included. Please see prompts.py

* Included guardrails that prevent users from:

  * Accessing or revealing the system prompt.
  * Modifying the system prompt directly.

* The model was instructed not to respond to questions regarding:

  * Cats or dogs
  * Horoscopes or Zodiac Signs
  * Taylor Swift
