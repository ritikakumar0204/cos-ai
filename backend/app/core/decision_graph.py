from datetime import datetime, timezone
import networkx as nx


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def _decision_node_id(decision_id: str) -> str:
    return f"decision:{decision_id}"


def _version_node_id(version_id: str) -> str:
    return f"decision_version:{version_id}"


def _stakeholder_node_id(stakeholder_id: str) -> str:
    return f"stakeholder:{stakeholder_id}"


def init_graph() -> nx.DiGraph:
    """Initialize an empty directed graph."""
    return nx.DiGraph()


def add_decision(graph: nx.DiGraph, decision_id: str, title: str, created_at: str | None = None) -> str:
    """Add a decision node."""
    node_id = _decision_node_id(decision_id)
    graph.add_node(
        node_id,
        type="decision",
        decision_id=decision_id,
        title=title,
        created_at=created_at or _ts(),
    )
    return node_id


def add_decision_version(
    graph: nx.DiGraph,
    version_id: str,
    decision_id: str,
    content: str,
    confidence: float,
    reasoning: str,
    created_at: str | None = None,
) -> str:
    """
    Add a decision_version node and connect it to its decision with `has_version`.
    """
    decision_node = _decision_node_id(decision_id)
    if decision_node not in graph:
        raise ValueError(f"Decision '{decision_id}' does not exist.")

    version_node = _version_node_id(version_id)
    graph.add_node(
        version_node,
        type="decision_version",
        version_id=version_id,
        decision_id=decision_id,
        content=content,
        created_at=created_at or _ts(),
        confidence=float(confidence),
        reasoning=reasoning,
    )
    graph.add_edge(decision_node, version_node, type="has_version")
    return version_node


def link_supersedes(graph: nx.DiGraph, new_version_id: str, previous_version_id: str) -> None:
    """Link one decision_version to the version it supersedes."""
    new_node = _version_node_id(new_version_id)
    prev_node = _version_node_id(previous_version_id)

    if new_node not in graph:
        raise ValueError(f"Version '{new_version_id}' does not exist.")
    if prev_node not in graph:
        raise ValueError(f"Version '{previous_version_id}' does not exist.")

    graph.add_edge(new_node, prev_node, type="supersedes")


def add_stakeholder(graph: nx.DiGraph, stakeholder_id: str, name: str, role: str) -> str:
    """Add a stakeholder node."""
    node_id = _stakeholder_node_id(stakeholder_id)
    graph.add_node(
        node_id,
        type="stakeholder",
        stakeholder_id=stakeholder_id,
        name=name,
        role=role,
    )
    return node_id


def record_reference(graph: nx.DiGraph, version_id: str, stakeholder_id: str) -> None:
    """Record that a stakeholder referenced a specific decision version."""
    version_node = _version_node_id(version_id)
    stakeholder_node = _stakeholder_node_id(stakeholder_id)

    if version_node not in graph:
        raise ValueError(f"Version '{version_id}' does not exist.")
    if stakeholder_node not in graph:
        raise ValueError(f"Stakeholder '{stakeholder_id}' does not exist.")

    graph.add_edge(version_node, stakeholder_node, type="referenced_by")


def record_affects(graph: nx.DiGraph, decision_id: str, stakeholder_id: str) -> None:
    """Record that a decision affects a stakeholder."""
    decision_node = _decision_node_id(decision_id)
    stakeholder_node = _stakeholder_node_id(stakeholder_id)

    if decision_node not in graph:
        raise ValueError(f"Decision '{decision_id}' does not exist.")
    if stakeholder_node not in graph:
        raise ValueError(f"Stakeholder '{stakeholder_id}' does not exist.")

    graph.add_edge(decision_node, stakeholder_node, type="affects")
def debug_print_graph(G):
    print("\nNODES:")
    for node, data in G.nodes(data=True):
        print(node, data)

    print("\nEDGES:")
    for src, dst, data in G.edges(data=True):
        print(f"{src} -> {dst} : {data}")


# Small example scenario:
# - one decision
# - two versions
# - two stakeholders
# - each stakeholder references a different version
if __name__ == "__main__":
    g = init_graph()

    add_decision(g, decision_id="dec-1", title="Database for analytics pipeline")

    add_decision_version(
        g,
        version_id="v1",
        decision_id="dec-1",
        content="Use Postgres for analytics MVP",
        confidence=0.82,
        reasoning="Team familiarity and low setup complexity",
    )
    add_decision_version(
        g,
        version_id="v2",
        decision_id="dec-1",
        content="Switch to BigQuery for scale needs",
        confidence=0.74,
        reasoning="Projected event volume exceeds Postgres cost/perf target",
    )
    link_supersedes(g, new_version_id="v2", previous_version_id="v1")

    add_stakeholder(g, stakeholder_id="s-1", name="Alice", role="Product")
    add_stakeholder(g, stakeholder_id="s-2", name="Bob", role="Infra")

    record_reference(g, version_id="v1", stakeholder_id="s-1")
    record_reference(g, version_id="v2", stakeholder_id="s-2")

    record_affects(g, decision_id="dec-1", stakeholder_id="s-1")
    record_affects(g, decision_id="dec-1", stakeholder_id="s-2")
    debug_print_graph(g)

