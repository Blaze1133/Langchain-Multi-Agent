from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools.tool import web_search, scrape_webpage
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b")

# building the first agent


def build_search_agent():
    agent = create_agent(
        model=llm,
        tools=[web_search]
    )
    return agent


def build_reader_agent():
    agent = create_agent(
        model=llm,
        tools=[scrape_webpage]
    )
    return agent

# next step is to create a writer prompt


writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a expert  research writer. Write clear, strcutured and insightful reports"),
    ("user", """Please write a detailed article based on the following topic

     Topic: {topic}
     Research gathered: {research}

     Structure the report as:
     - Introduction
     - Key Findings (minimum 3 well explained points)
     - Conclusion
     - Sources (list all URLS found in the research)


     """)])

writer_chain = writer_prompt | llm | StrOutputParser()


critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a expert research critic. You will review the article and provide feedback on the content, structure, and clarity of the report. Your feedback should be constructive and actionable."),
    ("user", """Please review the following article and provide feedback on the content, structure, and clarity of the report. Your feedback should be constructive and actionable.

     Article: {article}

     Respond in this exact format:
        Score: X/10
        Strengths: (list the strengths of the article)
        Weaknesses: (list the weaknesses of the article)
        Areas for Improvement: (list specific areas where the article can be improved)
        One line verdict: (provide a one line summary of your overall assessment of the article)
     """)])
critic_chain = critic_prompt | llm | StrOutputParser()
