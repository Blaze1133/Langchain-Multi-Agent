from collections.abc import Callable

from agent.agent import build_search_agent, build_reader_agent, writer_chain, critic_chain


def run_research_pipeline(
    topic: str,
    on_stage: Callable[[str], None] | None = None,
    verbose: bool = True,
) -> dict:
    state = {}

    def notify(stage: str) -> None:
        if on_stage:
            on_stage(stage)

    # search agent working
    notify("search")
    if verbose:
        print("\n" + "="*50)
        print("Step 1 - Search agent is working")
        print("="*50)

    search_agent = build_search_agent()
    search_results = search_agent.invoke({
        "messages": [("user", f"Find recent, and reliable infromation about the : {topic}")]
    })
    state["search_results"] = search_results["messages"][-1].content

    if verbose:
        print("\n search result", state["search_results"])

    # step 2 configuring the reader agent
    notify("read")
    if verbose:
        print("\n" + "="*50)
        print("Step 2 - Reader agent is working")
        print("="*50)

    reader_agent = build_reader_agent()
    reader_results = reader_agent.invoke({
        "messages": [("user", f"Please read the following research and extract the key points and insights: {state['search_results']}")]
    })

    state["reader_results"] = reader_results["messages"][-1].content
    if verbose:
        print("\n reader results", state["reader_results"])

    # step 3 configuring the writer chain
    notify("write")
    if verbose:
        print("\n" + "="*50)
        print("Step 3 - Writer chain is working")
        print("="*50)

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": state["reader_results"]
    })
    if verbose:
        print("\n FINAL REPORT", state["report"])

    # step 4 configuring the critic chain
    notify("review")
    if verbose:
        print("\n" + "="*50)
        print("Step 4 - Critic chain is working")
        print("="*50)

    state["critic_feedback"] = critic_chain.invoke({
        "article": state["report"]
    })
    if verbose:
        print("\n CRITIC FEEDBACK", state["critic_feedback"])

    return state
