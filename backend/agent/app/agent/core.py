from langchain.agents import create_agent
from langchain_community.chat_models.tongyi import ChatTongyi
from app.config import settings
from app.agent.tools import tools
from app.agent.prompt import SYSTEM_PROMPT


def create_agent_executor():
    llm = ChatTongyi(
        model=settings.llm_model,
        api_key=settings.dashscope_api_key,
        streaming=True,
        model_kwargs={
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
        },
    )

    return create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)
