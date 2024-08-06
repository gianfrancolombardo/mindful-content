from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain_core.messages import AIMessage
import json
import cachetools

from lunary import LunaryCallbackHandler

class MovieAnalyzer:
    def __init__(self, 
                base_url="http://localhost:1234/v1", 
                api_key="not-needed", 
                temperature=0):
        
        handler = LunaryCallbackHandler(app_id="508ded07-b3ab-40c1-b4c4-91b34bac5b98")
        
        self.chat = ChatOpenAI(
            base_url=base_url, 
            api_key=api_key,
            temperature=temperature
            ,callbacks=[handler]
        )
        self.prompts = {
            "system": """
                    You are a helpful assistant with a lot of knowledge about movies, series and tv shows, its actors, plot, and scripts. 
                    You knowledge isn't infinite, if you don't know the movie or series you just say I don't know.
                    You are also a professional creating json objects and you know its structure. IMPORTANT: If a json object is requested, you only have to answer the code.
            """,
            "prompt_1": """
                    Do you know the movie {movie} from the year {year}?
                    Provide detailed information on the representation of genders, ethnicities, and other possible biases in this film.
                    At the end of your response add a JSON object with the key "is_there_information" and value boolean.""",
            "prompt_2": """
                    Explain the criteria required for a movie to pass the {test} test, which evaluates {test_objective}.
                    2. Analyze whether the movie meets these criteria, providing a step-by-step rationale for your conclusion.
            """,
            "prompt_3": """
                    Based on your analysis, provide a JSON object with the following structure:
                    - result: (boolean)
                    - reason: (a simple sentence with passed or not this test specific for this movie, be specific). 
                    Important: Just the json object, nothing else.
            """,
            "system_translate": """
                    It acts like a professional translator who always gives a translation regardless of the context.
                    Don't translate the names of the movies.
            """,
            "prompt_translate": """
                    Give me just a JSON object with key "translated" and  contain the translation to {language} of:
                    "{text}"
            """,
            "system_summary": """
                    You are a professional summarizer and content creator with a strong radical feminist perspective who can summarize in a concise way and ensure that each word adds value to the summary, 
                    aimed at a non-technical audience. 
                    You create short really viral content focused on social networks.
                    Avoid using the term "people of color"; use "afrodescendant" instead. 
                    Avoid using double quotation marks (") in your response because they cause errors in JSON formatting. Use single quotation marks (') instead. 
            """,
            "prompt_summary": """
                    {results}
                    Based on the previous test results for the movie "{movie}" ({year}), 
                    create a concise summary for social media that highlights the implications of the biases found in the movie. 
                    Do not mention the tests themselves. Avoid hashtags.
            """
        }

        self.default_empty_object = {
            "result": None,
            "reason": "Insufficient information to determine if the movie passes the test",
            "reason_es": "Información insuficiente para determinar si la película pasa la prueba",
        }

        self.cache = cachetools.LRUCache(maxsize=100)

    def get_cache(self, movie, year):
        """ Get the value from the cache. """
        key = (movie, year)
        return self.cache.get(key)

    def set_cache(self, movie, year, value):
        """ Set the value in the cache. """
        key = (movie, year)
        self.cache[key] = value

    def clear_cache(self):
        """ Clear the cache. """
        self.cache.clear()

    def run(self, movie, year, test, test_objective):
        """ Analyzing a movie, utilizing caching and chat history. """
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
        
        # The model know the movie?
        if not self.is_there_information(response_1):
            return self.return_default_empty_object()

        # Step 2
        prompt_2 = PromptTemplate.from_template(self.prompts["prompt_2"])
        chat_history.add_user_message(prompt_2.format(test=test, test_objective=test_objective))
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
            return self.return_default_empty_object()
    
    def translate(self, text, target_language="en"):
        """ Translates the text to the target language. """
        try:
            chat_history = ChatMessageHistory()
            json_parser = SimpleJsonOutputParser()
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prompts["system_translate"]),
                MessagesPlaceholder(variable_name="messages"),
            ])

            chain_translate = prompt_template | self.chat

            prompt_translate = PromptTemplate.from_template(self.prompts["prompt_translate"])
            chat_history.add_user_message(prompt_translate.format(language=target_language, text=text))
            response = chain_translate.invoke({"messages": chat_history.messages})
            chat_history.add_ai_message(response)
            
            result = json_parser.parse(response.content)
            return result
        except Exception as e:
            print("Error translating", e)
            return None
        

    def summary(self, movie):
        """ Make a summary of the tests' results of a movie. """
        try:
            chat_history = ChatMessageHistory()
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prompts["system_summary"]),
                MessagesPlaceholder(variable_name="messages"),
            ])

            chain_summary = prompt_template | self.chat

            results_str = ""
            for test in movie['result_test']:
                results_str += f"{test['tests']['name']} ({test['tests']['objective']}): {'Passed' if test['result'] else 'Failed' if test['result'] is False else 'Incomplete'} \n"
            
            prompt_summary = PromptTemplate.from_template(self.prompts["prompt_summary"])
            chat_history.add_user_message(prompt_summary.format(movie=movie['title'], year=movie['year'], results=results_str))
            response = chain_summary.invoke({"messages": chat_history.messages})
            chat_history.add_ai_message(response)
            
            return response.content
        except Exception as e:
            print("Error summating", e)
            return None
    
    def is_there_information(self, ai_message: AIMessage) -> dict:
        """ Extracts the JSON object from the AI message and check if there is information """
        try:
            start_index = ai_message.content.find("{")
            end_index = ai_message.content.rfind("}")
            json_str = ai_message.content[start_index:end_index+1]
            if not json_str:
                return False
            obj_response = json.loads(json_str)
            
            if 'is_there_information' in obj_response:
                return obj_response['is_there_information']
            else:
                return False
        except Exception as e:
            return False
        
    def return_default_empty_object(self):
        """ Returns a default empty object with the test name. """
        return self.default_empty_object