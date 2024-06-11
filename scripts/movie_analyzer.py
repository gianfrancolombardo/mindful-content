from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain_core.messages import AIMessage
import json
import logging
import cachetools

class MovieAnalyzer:
    def __init__(self, 
                 base_url="http://localhost:1234/v1", 
                 api_key="not-needed", 
                 temperature=0):
        
        self.chat = ChatOpenAI(
            base_url=base_url, 
            api_key=api_key,
            temperature=temperature
        )
        self.prompts = {
            "system": """
                    You are a helpful assistant with a lot of knowledge about movies, series and tv shows, its actors, plot, and scripts. 
                    You knowledge isn't infinite, if you don't know the movie or series you just say I don't know.
                    You are also a professional creating json objects and you know its structure. IMPORTANT: If a json object is requested, you only have to answer the code.
            """,
            "prompt_1": """
                    Do you know the movie {movie} of year {year}? 
                    If you don't know, don't answer the question, just return a JSON Object with key result and value null, nothing else.""",
            "prompt_2": """
                    1. Tell me the keys to know if a movie passes the {test} test.
                    2. Then tell me if this movie does it or not.
                    Think step by step.
            """,
            "prompt_3": """
                    Now give me a JSON object with this previous data, with 2 keys: "result" (boolean) and "reason" (a simple sentence with passed or not this test specific for this movie, be specific). 
                    Important: Just the json object, nothing else.
            """,
            "system_transtale": """
                    It acts like a professional translator who always gives a translation regardless of the context.
            """,
            "prompt_transtale": """
                    Translate the following text into {language}: 
                    {text}
                    Output format: JSON object with key: translated containing the translation to the requested language
            """
        }

        self.default_empty_object = {
            "result": None,
            "reason": "Insufficient information to determine if the movie passes the test",
            "reason_es": "Información insuficiente para determinar si la película pasa la prueba",
        }

        # import os
        # os.environ["LANGCHAIN_TRACING_V2"] = "true"
        # os.environ["LANGCHAIN_API_KEY"] = "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"
        # os.environ["LANGCHAIN_PROJECT"] = "mindful-content-01"

        self.cache = cachetools.LRUCache(maxsize=100)

    def get_cache(self, movie, year):
        key = (movie, year)
        return self.cache.get(key)

    def set_cache(self, movie, year, value):
        key = (movie, year)
        self.cache[key] = value

    def run(self, movie, year, test):
        chat_history = ChatMessageHistory()
        json_parser = SimpleJsonOutputParser()
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.prompts["system"]),
            MessagesPlaceholder(variable_name="messages"),
        ])

        chain = prompt_template | self.chat

        
        # Step 1
        prompt_1 = PromptTemplate.from_template(self.prompts["prompt_1"])
        chat_history.add_user_message(prompt_1.format(movie=movie, year=year))
        
        response_1 = self.get_cache(movie, year)
        if not response_1:
            # Not in cache
            response_1 = chain.invoke({"messages": chat_history.messages})
            self.set_cache(movie, year, response_1)
        chat_history.add_ai_message(response_1)
        
        # If the response is a JSON object, Model don't know the movie
        if self.force_parse_json(response_1):
            return self.return_default_empty_object(test)

        # Step 2
        prompt_2 = PromptTemplate.from_template(self.prompts["prompt_2"])
        chat_history.add_user_message(prompt_2.format(test=test))
        response_2 = chain.invoke({"messages": chat_history.messages})
        chat_history.add_ai_message(response_2)

        # Step 3
        prompt_3 = PromptTemplate.from_template(self.prompts["prompt_3"])
        chat_history.add_user_message(prompt_3.format())
        response_3 = chain.invoke({"messages": chat_history.messages})
        chat_history.add_ai_message(response_3)
        
        try:
            result = json_parser.parse(response_3.content)
            return result
        except Exception as e:
            print("Parsing json", e)
            return self.return_default_empty_object(test)
    
    def translate(self, text, target_language="en"):
        """Translates the text to the target language."""
        try:
            chat_history = ChatMessageHistory()
            json_parser = SimpleJsonOutputParser()
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prompts["system_transtale"]),
                MessagesPlaceholder(variable_name="messages"),
            ])

            chain_translate = prompt_template | self.chat

            prompt_translate = PromptTemplate.from_template(self.prompts["prompt_transtale"])
            chat_history.add_user_message(prompt_translate.format(language=target_language, text=text))
            response = chain_translate.invoke({"messages": chat_history.messages})
            chat_history.add_ai_message(response)
            
            result = json_parser.parse(response.content)
            return result
        except Exception as e:
            return str(e)
    
    def force_parse_json(self, ai_message: AIMessage) -> dict:
        """Extracts the JSON object from the AI message and converts it to a Python object."""
        try:
            start_index = ai_message.content.find("{")
            end_index = ai_message.content.rfind("}")
            json_str = ai_message.content[start_index:end_index+1]
            if not json_str:
                return None
            return json.loads(json_str)
        except Exception as e:
            return None
        
    def return_default_empty_object(self, test):
        """Returns a default empty object with the test name."""
        obj = self.default_empty_object
        #obj['test'] = test
        return obj