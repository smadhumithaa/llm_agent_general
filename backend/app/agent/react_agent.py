from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

from app.core.config import get_settings
from app.tools.web_search import web_search
from app.tools.api_tools import get_weather, get_news
from app.tools.code_executor import execute_python
from app.tools.doc_summarizer import summarize_document

settings = get_settings()

ALL_TOOLS = [web_search, get_weather, get_news, execute_python, summarize_document]

REACT_PROMPT = PromptTemplate.from_template("""You are Aria, an intelligent general-purpose AI assistant.
You have access to tools to help answer questions accurately and completely.

TOOLS:
------
{tools}

TOOL NAMES: {tool_names}

INSTRUCTIONS:
- Always think step-by-step before choosing a tool.
- Use tools when you need current information, calculations, or file content.
- After getting a tool result, reflect on whether it fully answers the question.
- If one tool is not enough, use multiple tools in sequence.
- Be concise but complete in your Final Answer.
- Never fabricate information - if unsure, say so.

FORMAT (strictly follow this):
Question: the input question
Thought: your reasoning about what to do
Action: one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to answer
Final Answer: your complete answer to the original question

Begin!

Previous conversation:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}""")

_memories: dict[str, ConversationBufferWindowMemory] = {}


def get_memory(session_id: str) -> ConversationBufferWindowMemory:
    if session_id not in _memories:
        _memories[session_id] = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            return_messages=False,
        )
    return _memories[session_id]


def clear_memory(session_id: str) -> None:
    _memories.pop(session_id, None)


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "resourceexhausted" in msg or "quota exceeded" in msg or "429" in msg


def _candidate_models() -> list[str]:
    raw = [settings.GEMINI_MODEL]
    if settings.GEMINI_FALLBACK_MODELS.strip():
        raw.extend(settings.GEMINI_FALLBACK_MODELS.split(","))

    seen: set[str] = set()
    models: list[str] = []
    for value in raw:
        name = value.strip()
        if name and name not in seen:
            seen.add(name)
            models.append(name)
    return models


def build_agent_executor(session_id: str, model_name: str) -> AgentExecutor:
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2,
        max_retries=settings.GEMINI_MAX_RETRIES,
    )

    agent = create_react_agent(
        llm=llm,
        tools=ALL_TOOLS,
        prompt=REACT_PROMPT,
    )

    memory = get_memory(session_id)

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        memory=memory,
        verbose=settings.AGENT_VERBOSE,
        max_iterations=settings.MAX_ITERATIONS,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


def run_agent(question: str, session_id: str) -> dict:
    """
    Run the ReAct agent and return:
    - answer: final answer string
    - steps: list of (tool_name, tool_input, observation) for frontend display
    - session_id
    """
    result = None
    last_quota_error: Exception | None = None
    models = _candidate_models()

    for model_name in models:
        executor = build_agent_executor(session_id, model_name)
        try:
            result = executor.invoke({"input": question})
            break
        except Exception as e:
            if _is_quota_error(e):
                last_quota_error = e
                continue
            raise

    if result is None:
        if last_quota_error is not None:
            tried = ", ".join(models)
            raise RuntimeError(
                f"All configured Gemini models are quota-limited: {tried}. "
                "Use a key/project with available quota or enable billing."
            ) from last_quota_error
        raise RuntimeError("Agent failed to produce a response.")

    steps = []
    for action, observation in result.get("intermediate_steps", []):
        steps.append(
            {
                "tool": action.tool,
                "input": action.tool_input,
                "observation": str(observation)[:500],
            }
        )

    return {
        "answer": result["output"],
        "steps": steps,
        "session_id": session_id,
        "tool_count": len(steps),
    }
