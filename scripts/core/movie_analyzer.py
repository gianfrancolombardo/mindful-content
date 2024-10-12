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
                model="gpt-4o-mini",
                temperature=0):
        
        handler = LunaryCallbackHandler(app_id="508ded07-b3ab-40c1-b4c4-91b34bac5b98")
        
        self.chat = ChatOpenAI(
            base_url=base_url, 
            api_key=api_key,
            temperature=temperature,
            model=model
            ,callbacks=[handler]
        )
        self.prompts = {
            "system": """
                    You are an advanced AI assistant with extensive knowledge of movies, series, TV shows, actors, plot details, and scripts. 
                    Your responses are designed to help users navigate this information with accuracy and detail. Your knowledge, however, is not infinite; if you're unfamiliar with a movie or series, state clearly, "I don't know." Additionally, you are skilled in creating JSON objects with perfect syntax and structure. 
                    Avoid using the term 'people of color' and instead use 'afrodescendant'.
                    Your responses should always follow this structure:

                    1. Begin with a <thinking> section where you:
                        a. Analyze the request and the information provided.
                        b. Clearly outline your approach, identifying necessary steps.
                        c. Break down your reasoning using "Chain of Thought" when necessary, especially if it involves complex analysis.

                    2. For each key decision or piece of reasoning, include a <reflection> section where you:
                        a. Review your analysis.
                        b. Check for potential mistakes or missing details.
                        c. Validate or adjust your conclusion, if necessary.

                    3. Close all <reflection> sections and the <thinking> section with their respective closing tags.

                    4. If requested, provide a detailed response in an <output> section, including any additional context or explanations.

                    5. When a JSON object is requested:
                        - Answer with correct JSON syntax, no additional comments, or explanations outside the code block.
                        - Ensure the structure is clean and correct.

                    Remember to follow the tag format (<thinking>, <reflection>, <output>) throughout your responses. Be thorough in your reasoning, and provide clarity and precision at each step.
                    If a movie or series is outside your knowledge, promptly indicate so and move on to the next inquiry.
            """,
            "prompt_1": """
                    Do you know the movie {movie} from the year {year}?
                    Provide detailed information on the representation of genders, ethnicities, and other possible biases in this film.
                    Only for this response: at the end of your response add a JSON object with the key "is_there_information" and value boolean.""",
            "prompt_2": """
                    The criteria: {test_criteria}
                    Task: Analyze whether the movie {movie} ({year}) meets these criteria, providing a step-by-step rationale for your conclusion.
            """,
            "prompt_3": """
                    Based on your analysis, provide a JSON object with the following structure:
                    - result: (boolean)
                    - reason: (a simple sentence with passed or not this test specific for this movie, be specific). 
                    - reason_es: (the same reason in Spanish)
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
                    You are a professional content creator and summarizer with a strong radical feminist perspective. You can summarize concisely, ensuring that each word adds value to the summary, aimed at a non-technical audience. 
                    You create short, highly viral content focused on social media.
                    Your responses should always follow this structure:

                    1. Begin with a <thinking> section where you:
                        a. Analyze the request and the provided content.
                        b. Clearly outline your approach for creating the summary or viral content.
                        c. Break down your reasoning using 'Chain of Thought' if necessary, especially to ensure a strong radical feminist approach.

                    2. For each key decision or part of your reasoning, include a <reflection> section where you:
                        a. Review your analysis.
                        b. Check for potential mistakes or if the content can be optimized.
                        c. Validate or adjust your conclusion if necessary.

                    3. Close all <reflection> and <thinking> sections with their respective closing tags.

                    4. If requested, provide a summary or content in an <output> section, ensuring it is brief, clear, and impactful for social media.

                    5. When creating viral content:
                        - Avoid using the term 'people of color' and instead use 'afrodescendant'.
                        - Avoid using double quotation marks (") in your response to prevent JSON formatting errors; use single quotation marks (') instead.

                    Remember to follow the tag format (<thinking>, <reflection>, <output>) throughout your responses. Be concise, clear, and direct, optimizing the content to be viral on social media while ensuring a strong radical feminist perspective in each step.

            """,
            "prompt_summary": """
                    {results}
                    Based on the previous test results for the movie "{movie}" ({year}), 
                    create a concise summary for social media with educational and informative tone, that highlights the implications of the biases found in the movie. 
                    Do not mention the tests themselves. Avoid hashtags.
                    At the end of your response add a JSON object with the key "summary_in_spanish" with the summary in Spanish.
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

    def run(self, movie, year, test_criteria):
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
        chat_history.add_user_message(prompt_2.format(
            test_criteria=test_criteria,
            movie=movie, 
            year=year))
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

            obj_summary = self.get_json(response)
            if obj_summary is None:
                summary = self.get_output_tags(response)
            else:
                summary = obj_summary['summary_in_spanish']
            
            return summary
        except Exception as e:
            print("Error summating", e)
            return None
    
    def is_there_information(self, ai_message: AIMessage) -> dict:
        """ Extracts the JSON object from the AI message and check if there is information """
        try:
            obj_response = self.get_json(ai_message)
            
            if 'is_there_information' in obj_response:
                return obj_response['is_there_information']
            else:
                return False
        except Exception as e:
            return False
        
    def get_json(self, ai_message: AIMessage) -> dict:
        """ Extracts the JSON object from the AI message. """
        try:
            start_index = ai_message.content.find("{")
            end_index = ai_message.content.rfind("}")
            json_str = ai_message.content[start_index:end_index+1]
            if not json_str:
                return None
            return json.loads(json_str)
        except Exception as e:
            return None

    def get_output_tags(self, ai_message: AIMessage) -> dict:
        """ Extracts text into the tag <output> from the AI message. """
        try:
            start_index = ai_message.content.find("<output>")
            end_index = ai_message.content.rfind("</output>")
            return ai_message.content[start_index:end_index+9]
        except Exception as e:
            return None
        
        
    def return_default_empty_object(self):
        """ Returns a default empty object with the test name. """
        return self.default_empty_object.copy()