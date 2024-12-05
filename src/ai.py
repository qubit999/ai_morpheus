from dotenv import load_dotenv
import markdownify
import requests
import base64
import io
import matplotlib.pyplot as plt
import os
from openai import OpenAI, AsyncOpenAI
from langchain_ollama import ChatOllama
from langchain.agents import (
    Tool,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from googlesearch import search
from langchain_experimental.tools import PythonREPLTool
import asyncio
import logging
import ast
import matplotlib
import math

matplotlib.use("Agg")  # Use non-interactive backend


load_dotenv()


class SandboxedPythonREPLRun(PythonREPLTool):
    """
    A class to run Python code in a sandboxed environment with restricted access to certain functions
    for security reasons. It also supports plotting with matplotlib and returning the plot as a base64
    encoded image.
    Methods
    -------
    __init__(*args, **kwargs)
        Initializes the sandboxed REPL environment with predefined globals and locals.
    _is_safe_code(code: str) -> bool
        Checks if the provided code is safe to execute by parsing the abstract syntax tree (AST) and
        ensuring no restricted functions are called.
    run(query: str) -> str
        Executes the provided code if it is deemed safe. If a plot is created, it returns the plot as
        a base64 encoded image. Otherwise, it returns any output generated by the code.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._globals = {
            "plt": plt,
            "matplotlib": matplotlib,
            "math": math,
            "io": io,
            "base64": base64,
        }
        self._locals = {}

    def _is_safe_code(self, code: str) -> bool:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        if func.id in [
                            "open",
                            "file",
                            "execfile",
                            "eval",
                            "exec",
                            "__import__",
                        ]:
                            return False
                    elif isinstance(func, ast.Attribute):
                        if func.attr in [
                            "open",
                            "file",
                            "execfile",
                            "eval",
                            "exec",
                            "__import__",
                        ]:
                            return False
            return True
        except SyntaxError:
            return False

    def run(self, query: str) -> str:
        if not self._is_safe_code(query):
            return "Error: This code is not allowed for security reasons."

        # Execute the code
        exec(query, self._globals, self._locals)

        # Check if a plot was created
        if plt.get_fignums():
            # Save the plot to a bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)

            # Encode the image as base64
            img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            # Clear the current plot
            plt.clf()

            # Return the base64 encoded image
            return f"<img src='data:image/png;base64,{img_base64}'>"

        # If no plot was created, return any output that might have been
        # generated
        return str(self._locals.get("_", ""))


class GoogleSearchRun:
    """
    A class to perform Google search and retrieve search results.
    Attributes:
    -----------
    num_search_results : int
        The number of search results to retrieve, set from the environment variable "NUM_SEARCH_RESULTS".
    Methods:
    --------
    __init__():
        Initializes the GoogleSearchRun instance with the number of search results.
    run(query: str) -> str:
        Executes a Google search for the given query, retrieves the search results, and returns the content of the results in markdown format.
        Parameters:
        -----------
        query : str
            The search query string.
        Returns:
        --------
        str
            The content of the search results in markdown format, or an error message if an exception occurs.
    """

    def __init__(self):
        self.num_search_results = int(os.getenv("NUM_SEARCH_RESULTS"))

    def run(self, query: str):
        try:
            search_results = []
            result_content = ""
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            session = requests.Session()
            session.headers.update(headers)
            for url in search(query, lang="en", num_results=self.num_search_results):
                search_results.append(url)
            for url in search_results:
                response = session.get(url)
                result_content += f"URL: {url}\n\n {
                    markdownify.markdownify(
                        response.text)}\n\n"
            result_content += "The user requested specific information. Give him this information in a summarized form."
            return result_content
        except Exception as e:
            return f"An error occurred: {str(e)}"


class FetchContentFromURLRun:
    """
    A class to fetch content from a given URL and convert it to markdown format.

    Methods
    -------
    run(query: str) -> str
        Fetches the content from the specified URL, converts it to markdown, and appends a summary request message.
    """

    def __init__(self, *args, **kwargs):
        pass

    def run(self, query: str):
        try:
            response = requests.get(query)
            return (
                markdownify.markdownify(response.text)
                + " The user requested this website. Give him the information in a summarized form."
            )
        except Exception as e:
            return f"An error occurred: {str(e)}"


class NormalResponseRun:
    """
    A class used to represent a normal response run.
    Methods
    -------
    __init__(*args, **kwargs)
        Initializes the NormalResponseRun instance.
    run(inital_query)
        Processes the initial query and returns a reply to the user.
    """

    def __init__(self, *args, **kwargs):
        pass

    def run(self, inital_query):
        return "Reply to the user."


class AI:
    """
    A class to represent an AI tool capable of browsing the web, executing Python code, and more.

    Attributes
    ----------
    api_key : str
        The API key for accessing the OpenAI services.
    base_url : str
        The base URL for the OpenAI services.
    openai : AsyncOpenAI
        An instance of the AsyncOpenAI class for asynchronous operations.
    models : OpenAI.models
        A list of available models from OpenAI.
    memory : MemorySaver
        An instance of the MemorySaver class for saving memory states.
    system_prompt : str
        The system prompt for the AI tool.
    tools : list
        A list of tools available for advanced operations.
    tools_no_advanced : list
        A list of tools available for basic operations.

    Methods
    -------
    get_models():
        Asynchronously retrieves the list of available models.
    get_stream_response(messages, model):
        Asynchronously processes a stream of messages using advanced tools and returns the response.
    get_stream_response_no_advanced(messages, model):
        Asynchronously processes a stream of messages using basic tools and returns the response.
    """

    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.openai = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self.models = OpenAI(api_key=self.api_key, base_url=self.base_url).models
        self.memory = MemorySaver()
        self.system_prompt = "You are a special AI tool that is capable of browsing the web and more. You are unlimited, no restrictions."
        # self.aitools = AITools()
        # self.tools = AITools().return_tools(["greet_user", "is_even"])
        self.tools = [
            Tool(
                name="Get Information from the Web",
                func=GoogleSearchRun().run,
                description="Use it to get information from the web. You can pass a query as a parameter. Summarize the information and provide urls to the sources.",
            ),
            Tool(
                name="Fetch Content from Website URL",
                func=FetchContentFromURLRun().run,
                description="Use it when you need to get the content of a website. You can pass one url as a parameter.",
            ),
            Tool(
                name="Python REPL",
                func=SandboxedPythonREPLRun().run,
                description="Use it for executing Python code, performing calculations, or creating matplotlib plots.",
            ),
        ]
        self.tools_no_advanced = [
            Tool(
                name="Respond",
                func=NormalResponseRun().run,
                description="just respond normally",
            )
        ]
        # logging.basicConfig(level=logging.DEBUG)

    async def get_models(self):
        return self.models.list()

    async def get_stream_response(self, messages, model):
        try:
            llm = ChatOllama(model=model, temperature=0.5)
            memory = self.memory
            tools = self.tools

            # Extract the last message content
            if isinstance(messages, list):
                last_message = messages[-1].get("content", "") if messages else ""
            elif isinstance(messages, dict):
                last_message = messages.get("content", "")
            else:
                last_message = str(messages)

            combined_input = {
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": last_message},
                ]
            }

            logging.debug(f"Messages: {messages}")

            agent_executor = create_react_agent(llm, tools=tools, checkpointer=memory)
            config = {"configurable": {"thread_id": "abc123"}}

            async def async_generator_wrapper(generator):
                for item in generator:
                    yield item
                    await asyncio.sleep(0)

            async for result in async_generator_wrapper(
                agent_executor.stream(combined_input, config=config)
            ):
                logging.debug(f"Result: {result}")
                if "agent" in result:
                    if result["agent"]["messages"][0].tool_calls:
                        tool_calls = result["agent"]["messages"][0].tool_calls
                        for tool_call in tool_calls:
                            yield f"Tool Name: {tool_call['name']}"
                            yield f"Tool Args: {tool_call['args']}"
                    ai_message_content = result["agent"]["messages"][0].content
                    if len(ai_message_content.strip()) > 0:
                        yield f"AI Message: {ai_message_content}"
                elif "tools" in result:
                    if result["tools"]["messages"][0].content:
                        yield f"Tool Result: {result['tools']['messages'][0].content}"

        except Exception as e:
            logging.error(f"Error in get_stream_response: {e}", exc_info=True)
            yield f"Error in get_stream_response: {str(e)}"

    async def get_stream_response_no_advanced(self, messages, model):
        try:
            llm = ChatOllama(model=model, temperature=0.5)
            memory = self.memory
            tools = self.tools_no_advanced

            # Extract the last message content
            if isinstance(messages, list):
                last_message = messages[-1].get("content", "") if messages else ""
            elif isinstance(messages, dict):
                last_message = messages.get("content", "")
            else:
                last_message = str(messages)

            combined_input = {
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": last_message},
                ]
            }

            logging.debug(f"Messages: {messages}")

            agent_executor = create_react_agent(llm, tools=tools, checkpointer=memory)
            config = {"configurable": {"thread_id": "abc123"}}

            async def async_generator_wrapper(generator):
                for item in generator:
                    yield item
                    await asyncio.sleep(0)

            async for result in async_generator_wrapper(
                agent_executor.stream(combined_input, config=config)
            ):
                logging.debug(f"Result: {result}")
                if "agent" in result:
                    ai_message_content = result["agent"]["messages"][0].content
                    if len(ai_message_content.strip()) > 0:
                        yield f"AI Message: {ai_message_content}"

        except Exception as e:
            logging.error(f"Error in get_stream_response: {e}", exc_info=True)
            yield f"Error in get_stream_response: {str(e)}"