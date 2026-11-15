
from langgraph.graph import StateGraph, START, END

from app.agents.qa_state import QAAgentState
from app.agents.explorer_node import explorer_node
from app.agents.planner_node import planner_node
from app.agents.executor_node import executor_node
from app.agents.investigator_node import investigator_node
from app.agents.reporter_node import reporter_node


# Decide whether the workflow can continue after exploration.
def route_after_explorer(state: QAAgentState) -> str:
    if state.get("workflow_status") == "failed":
        return "stop"

    return "continue"


# Decide whether the workflow can continue after planning.
def route_after_planner(state: QAAgentState) -> str:
    if state.get("workflow_status") == "failed":
        return "stop"

    return "continue"


# Create the workflow.
workflow = StateGraph(QAAgentState)


# Register nodes.
workflow.add_node("explorer", explorer_node)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("investigator", investigator_node)
workflow.add_node("reporter", reporter_node)


# Starting point.
workflow.add_edge(START, "explorer")


# Explorer: continue to planner or skip to reporter.
workflow.add_conditional_edges(
    "explorer",
    route_after_explorer,
    {
        "continue": "planner",
        "stop": "reporter"
    }
)


# Planner: continue to executor or skip to reporter.
workflow.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "continue": "executor",
        "stop": "reporter"
    }
)


# Execute tests, then investigate available failures.
workflow.add_edge("executor", "investigator")


# Generate the final report.
workflow.add_edge("investigator", "reporter")


# Finish the workflow.
workflow.add_edge("reporter", END)


# Compile the graph.
qa_agent_graph = workflow.compile()
