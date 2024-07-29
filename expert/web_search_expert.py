import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI

class WebSearchAgent:
    def __init__(self, env_path='.venv/.env'):
        self.env_path = env_path
        self.load_environment_variables(self.env_path)
        self.setup_agent()

    def load_environment_variables(self, env_path):
        load_dotenv(env_path)
        os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2')
        os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT')
        os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')
        os.environ['TAVILY_API_KEY'] = os.getenv('TAVILY_API_KEY')

    def setup_agent(self):
        try:
            instructions = """You are an assistant that helps retrieve information from the web based on user queries."""
            base_prompt = hub.pull("langchain-ai/openai-functions-template")
            prompt = base_prompt.partial(instructions=instructions)
            llm = ChatOpenAI(temperature=0)
            tavily_tool = TavilySearchResults()
            tools = [tavily_tool]
            agent = create_openai_functions_agent(llm, tools, prompt)
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
            )
        except Exception as e:
            print(f"Error setting up the agent: {e}")

    def return_query_response(self, query, more_context=None):
        try:
            result = self.agent_executor.invoke({"input": query+" "+more_context})
            return result
        except IndexError as e:
            print(f"IndexError: {e}")
            return None
        except Exception as e:
            print(f"An error occurred during the query: {e}")
            return None

# # Usage
# if __name__ == "__main__":
#     web_search_agent = WebSearchAgent()
#     prompt = "Which zones are safer for buying an apartment in Capital Federal?"
#     more_context = "Information should be based in Argentina, if neccesary, translate to spanish."
#     print(web_search_agent.return_query_response(prompt, more_context))
