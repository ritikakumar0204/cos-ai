import networkx as nx


def get_latest_decision_version(graph: nx.DiGraph, decision_id: str) -> str:
    """
    Return the node ID of the latest decision version for a decision.

    Latest is defined as a version node that is not superseded by any other
    version node belonging to the same decision.
    """
    decision_node = f"decision:{decision_id}"
    if decision_node not in graph or graph.nodes[decision_node].get("type") != "decision":
        raise ValueError(f"Decision '{decision_id}' does not exist.")

    version_nodes: list[str] = []
    for _, version_node, edge_data in graph.out_edges(decision_node, data=True):
        if edge_data.get("type") != "has_version":
            continue
        if graph.nodes[version_node].get("type") != "decision_version":
            continue
        version_nodes.append(version_node)

    if not version_nodes:
        raise ValueError(f"Decision '{decision_id}' has no versions.")

    superseded_versions: set[str] = set()
    version_set = set(version_nodes)
    for new_version in version_nodes:
        for _, previous_version, edge_data in graph.out_edges(new_version, data=True):
            if edge_data.get("type") != "supersedes":
                continue
            if previous_version in version_set:
                superseded_versions.add(previous_version)

    latest_versions = [version for version in version_nodes if version not in superseded_versions]

    if len(latest_versions) != 1:
        raise ValueError(
            f"Decision '{decision_id}' has {len(latest_versions)} latest versions; expected exactly 1."
        )

    return latest_versions[0]
