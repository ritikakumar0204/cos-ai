import networkx as nx


def detect_decision_drift(graph: nx.DiGraph, decision_id: str) -> dict:
    """
    Detect whether stakeholders are referencing different versions
    of the same decision.
    """
    decision_node = f"decision:{decision_id}"

    if decision_node not in graph or graph.nodes[decision_node].get("type") != "decision":
        return {
            "decision_id": decision_id,
            "drift_detected": False,
            "referenced_versions": [],
            "stakeholder_versions": {},
        }

    version_nodes: list[str] = []
    for _, target, edge_data in graph.out_edges(decision_node, data=True):
        if edge_data.get("type") != "has_version":
            continue
        if graph.nodes[target].get("type") != "decision_version":
            continue
        if graph.nodes[target].get("decision_id") != decision_id:
            continue
        version_nodes.append(target)

    stakeholder_versions: dict[str, list[str]] = {}
    referenced_versions: set[str] = set()

    for version_node in version_nodes:
        version_id = graph.nodes[version_node].get("version_id")
        if not version_id:
            continue

        for _, stakeholder_node, edge_data in graph.out_edges(version_node, data=True):
            if edge_data.get("type") != "referenced_by":
                continue
            if graph.nodes[stakeholder_node].get("type") != "stakeholder":
                continue

            stakeholder_id = graph.nodes[stakeholder_node].get("stakeholder_id")
            if not stakeholder_id:
                continue

            stakeholder_versions.setdefault(stakeholder_id, [])
            if version_id not in stakeholder_versions[stakeholder_id]:
                stakeholder_versions[stakeholder_id].append(version_id)
                referenced_versions.add(version_id)

    referenced_version_list = sorted(referenced_versions)
    drift_detected = len(referenced_version_list) > 1

    return {
        "decision_id": decision_id,
        "drift_detected": drift_detected,
        "referenced_versions": referenced_version_list,
        "stakeholder_versions": stakeholder_versions,
    }
