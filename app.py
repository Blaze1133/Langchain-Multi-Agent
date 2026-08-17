from __future__ import annotations

import re
from datetime import datetime

import streamlit as st

from pipelines.pipeline import run_research_pipeline


st.set_page_config(
    page_title="Relay — multi-agent research studio",
    page_icon=":material/hub:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AGENTS = {
    "Scout": {
        "icon": ":material/travel_explore:",
        "stage": "search",
        "eyebrow": "Source discovery agent",
        "summary": "Finds a compact set of timely, relevant sources with Tavily.",
        "result_key": "search_results",
    },
    "Reader": {
        "icon": ":material/chrome_reader_mode:",
        "stage": "read",
        "eyebrow": "Evidence synthesis agent",
        "summary": "Reads linked material and extracts the evidence worth carrying forward.",
        "result_key": "reader_results",
    },
    "Writer": {
        "icon": ":material/edit_note:",
        "stage": "write",
        "eyebrow": "Research writing agent",
        "summary": "Turns the evidence brief into a structured, sourced report.",
        "result_key": "report",
    },
    "Critic": {
        "icon": ":material/fact_check:",
        "stage": "review",
        "eyebrow": "Quality review agent",
        "summary": "Scores the draft and calls out strengths, gaps, and concrete revisions.",
        "result_key": "critic_feedback",
    },
}

STAGE_TO_AGENT = {agent["stage"]: name for name, agent in AGENTS.items()}


def init_state() -> None:
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("completed_stages", set())
    st.session_state.setdefault("run_time", None)
    st.session_state.setdefault("view_agent", "Scout")
    st.session_state.setdefault("research_question", "How are attention spans changing?")


def render_hero() -> None:
    """A static, editorial header for the research workspace."""
    st.html(
        """
        <style>
          .relay-hero {
            border-bottom: 1px solid #d6d3cc;
            padding: 1.5rem 0 1.75rem;
            margin-bottom: 1.4rem;
          }
          .relay-eyebrow {
            color: #657085;
            font: 600 .72rem/1.2 'IBM Plex Mono', monospace;
            letter-spacing: .1em;
            text-transform: uppercase;
            margin: 0 0 1rem;
          }
          .relay-heading-row {
            display: grid;
            grid-template-columns: minmax(0, 1.4fr) minmax(240px, .6fr);
            align-items: end;
            gap: 3rem;
          }
          .relay-heading {
            color: #202425;
            font: 400 clamp(2.5rem, 5vw, 4.8rem)/.93 'DM Serif Display', Georgia, serif;
            letter-spacing: -.045em;
            margin: 0;
          }
          .relay-heading em { color: #1f4b99; }
          .relay-intro {
            color: #606a78;
            font: 400 1rem/1.55 'DM Sans', sans-serif;
            margin: 0 0 .2rem;
          }
          .relay-intro strong { color: #202425; font-weight: 600; }
          @media (max-width: 680px) {
            .relay-heading-row { grid-template-columns: 1fr; gap: 1rem; }
          }
        </style>
        <section class="relay-hero" aria-label="Relay research studio">
          <p class="relay-eyebrow">Relay / multi-agent research studio</p>
          <div class="relay-heading-row">
            <h1 class="relay-heading">Research,<br><em>with a visible trail.</em></h1>
            <p class="relay-intro"><strong>Four specialist agents.</strong><br>One focused question moves from discovery to evidence, writing, and review—with every handoff available to inspect.</p>
          </div>
        </section>
        """
    )


def parse_sources(text: str) -> list[dict[str, str]]:
    """Turn the Scout tool's predictable Title/URL/Snippet response into source cards."""
    items = []
    for block in re.split(r"(?=Title:)", text):
        title = re.search(r"Title:\s*(.+)", block)
        url = re.search(r"URL:\s*(\S+)", block)
        snippet = re.search(r"Snippet:\s*([\s\S]+)", block)
        if title and url:
            items.append(
                {
                    "title": title.group(1).strip(),
                    "url": url.group(1).strip(),
                    "snippet": snippet.group(1).strip() if snippet else "",
                }
            )
    return items


def render_agent_overview(active_stage: str | None = None) -> None:
    st.markdown("#### Agent crew")
    columns = st.columns(4)
    completed = st.session_state.completed_stages
    for column, (name, agent) in zip(columns, AGENTS.items()):
        with column.container(border=True):
            st.markdown(f"{agent['icon']}  **{name}**")
            if agent["stage"] == active_stage:
                st.badge("Working", icon=":material/progress_activity:", color="blue")
            elif agent["stage"] in completed:
                st.badge("Complete", icon=":material/check_circle:", color="green")
            else:
                st.badge("Queued", icon=":material/schedule:", color="gray")
            st.caption(agent["summary"])


def render_sources(search_results: str) -> None:
    sources = parse_sources(search_results)
    if not sources:
        st.markdown(search_results)
        return

    st.caption(f"Scout shortlisted {len(sources)} sources. Open any source to inspect the original context.")
    for index, source in enumerate(sources, 1):
        with st.container(border=True):
            st.markdown(f"**{index:02d} · [{source['title']}]({source['url']})**")
            if source["snippet"]:
                st.caption(source["snippet"])


def extract_score(text: str) -> str | None:
    match = re.search(r"Score:\s*([^\n]+)", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def render_agent_work(agent_name: str, result: dict | None) -> None:
    agent = AGENTS[agent_name]
    st.markdown(f"### {agent['icon']} {agent_name}")
    st.caption(f"{agent['eyebrow']} · {agent['summary']}")

    if not result:
        with st.container(border=True):
            st.markdown("##### Ready when you are")
            st.write("Run a research question to see this agent’s actual handoff and output here.")
        return

    output = result[agent["result_key"]]
    if agent_name == "Scout":
        render_sources(output)
    elif agent_name == "Critic":
        score = extract_score(output)
        if score:
            metric, detail = st.columns([1, 4], vertical_alignment="center")
            metric.metric("Quality score", score)
            detail.caption("The Critic reviews the Writer’s draft after the report is generated. Treat this as an editorial signal, not a factual guarantee.")
        with st.container(border=True):
            st.markdown(output)
    else:
        with st.container(border=True):
            st.markdown(output)


def render_run_metadata() -> None:
    if not st.session_state.run_time:
        return
    st.caption(
        f"Last run completed {st.session_state.run_time.strftime('%d %b %Y · %H:%M')} "
        "· inspect each agent’s handoff above"
    )


init_state()

render_hero()

with st.form("research_brief", border=True):
    st.text_area(
        "Research question",
        key="research_question",
        height=96,
        placeholder="Ask a focused question worth investigating…",
    )
    run = st.form_submit_button(
        "Run the research crew",
        type="primary",
        icon=":material/rocket_launch:",
        width="content",
    )

crew_slot = st.empty()
status_slot = st.empty()

if run:
    question = st.session_state.research_question.strip()
    if not question:
        st.warning("Add a research question first.", icon=":material/edit:")
    else:
        st.session_state.result = None
        st.session_state.completed_stages = set()
        crew_slot.empty()
        with status_slot.status(
            "Dispatching the research crew…",
            expanded=True,
            state="running",
        ) as run_status:
            def on_stage(stage: str) -> None:
                agent_name = STAGE_TO_AGENT[stage]
                run_status.write(f"{AGENTS[agent_name]['icon']} **{agent_name}** is now working")
                stage_order = list(STAGE_TO_AGENT)
                stage_index = stage_order.index(stage)
                st.session_state.completed_stages = set(stage_order[:stage_index])
                with crew_slot.container():
                    render_agent_overview(active_stage=stage)

            try:
                st.session_state.result = run_research_pipeline(
                    question,
                    on_stage=on_stage,
                    verbose=False,
                )
                st.session_state.completed_stages = set(STAGE_TO_AGENT)
                st.session_state.run_time = datetime.now()
                run_status.update(
                    label="Research crew completed the run",
                    state="complete",
                    expanded=False,
                )
                st.toast("Research run complete", icon=":material/check_circle:")
            except Exception as error:
                run_status.update(
                    label="The research run stopped",
                    state="error",
                    expanded=True,
                )
                st.error(str(error), icon=":material/error:")

with crew_slot.container():
    render_agent_overview()

st.space("small")
selected_agent = st.segmented_control(
    "Inspect an agent’s work",
    options=list(AGENTS),
    format_func=lambda name: f"{AGENTS[name]['icon']} {name}",
    key="view_agent",
    selection_mode="single",
    required=True,
    width="stretch",
)

render_agent_work(selected_agent, st.session_state.result)
render_run_metadata()

st.space("large")
st.markdown("#### Multi-agent architecture")
with st.container(border=True):
    st.mermaid_chart(
        """
        flowchart LR
            Q[Research question] --> S[Scout\nweb search]
            S --> R[Reader\nsource extraction]
            R --> W[Writer\nstructured report]
            W --> C[Critic\nquality review]
            C --> O[Inspectable research trail]
        """,
        width="stretch",
    )
    st.caption("Each agent receives the prior handoff, performs one focused responsibility, and exposes its output in the workspace above.")

st.caption("Relay · personal multi-agent research workspace")
