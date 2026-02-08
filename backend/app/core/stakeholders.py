import networkx as nx


ALLOWED_ROLES = {"Owner", "Contributor", "Informed", "Affected", "Observer"}


def _stakeholder_node_id(stakeholder_id: str) -> str:
    """Build the canonical stakeholder node id."""
    return f"stakeholder:{stakeholder_id}"


def _decision_node_id(decision_id: str) -> str:
    """Build the canonical decision node id."""
    return f"decision:{decision_id}"


def _version_node_id(version_id: str) -> str:
    """Build the canonical decision version node id."""
    return f"decision_version:{version_id}"


def _require_valid_role(role: str) -> None:
    """Ensure stakeholder role is one of the fixed, supported roles."""
    if role not in ALLOWED_ROLES:
        allowed = ", ".join(sorted(ALLOWED_ROLES))
        raise ValueError(f"Invalid role '{role}'. Allowed roles: {allowed}.")


def _require_node(graph: nx.DiGraph, node_id: str, label: str, value: str) -> None:
    """Validate that a graph node exists before creating relationship edges."""
    if node_id not in graph:
        raise ValueError(f"{label} '{value}' does not exist.")


def add_stakeholder(
    graph: nx.DiGraph,
    stakeholder_id: str,
    name: str,
    department: str,
    role: str,
    scoped_projects: list[str],
) -> str:
    """Add or update a stakeholder node with validated role and project scope."""
    _require_valid_role(role)
    node_id = _stakeholder_node_id(stakeholder_id)
    graph.add_node(
        node_id,
        type="stakeholder",
        stakeholder_id=stakeholder_id,
        name=name,
        department=department,
        role=role,
        scoped_projects=list(scoped_projects),
    )
    return node_id


def link_stakeholder_to_decision(
    graph: nx.DiGraph,
    stakeholder_id: str,
    decision_id: str,
) -> None:
    """Link stakeholder to a decision as owner or contributor based on role."""
    stakeholder_node = _stakeholder_node_id(stakeholder_id)
    decision_node = _decision_node_id(decision_id)

    _require_node(graph, stakeholder_node, "Stakeholder", stakeholder_id)
    _require_node(graph, decision_node, "Decision", decision_id)

    role = graph.nodes[stakeholder_node].get("role")
    _require_valid_role(role)

    if role == "Owner":
        edge_type = "owns"
    elif role == "Contributor":
        edge_type = "contributes"
    else:
        raise ValueError(
            "Only stakeholders with role 'Owner' or 'Contributor' can be linked to a decision."
        )

    graph.add_edge(stakeholder_node, decision_node, type=edge_type)


def link_stakeholder_to_version(
    graph: nx.DiGraph,
    stakeholder_id: str,
    version_id: str,
) -> None:
    """Link stakeholder to a decision version as informed or affected based on role."""
    stakeholder_node = _stakeholder_node_id(stakeholder_id)
    version_node = _version_node_id(version_id)

    _require_node(graph, stakeholder_node, "Stakeholder", stakeholder_id)
    _require_node(graph, version_node, "Version", version_id)

    role = graph.nodes[stakeholder_node].get("role")
    _require_valid_role(role)

    if role == "Informed":
        edge_type = "informed_of"
    elif role == "Affected":
        edge_type = "affected_by"
    else:
        raise ValueError(
            "Only stakeholders with role 'Informed' or 'Affected' can be linked to a decision version."
        )

    graph.add_edge(stakeholder_node, version_node, type=edge_type)


def _stakeholders_for_edge(
    graph: nx.DiGraph,
    target_node: str,
    edge_type: str,
    expected_roles: set[str],
) -> set[str]:
    """Collect stakeholder ids connected to target by a specific incoming edge type."""
    stakeholder_ids: set[str] = set()
    for source, _, attrs in graph.in_edges(target_node, data=True):
        if attrs.get("type") != edge_type:
            continue
        node_data = graph.nodes[source]
        if node_data.get("type") != "stakeholder":
            continue
        role = node_data.get("role")
        if role not in expected_roles:
            continue
        stakeholder_id = node_data.get("stakeholder_id")
        if stakeholder_id:
            stakeholder_ids.add(stakeholder_id)
    return stakeholder_ids


def compute_routing_targets(
    graph: nx.DiGraph,
    decision_id: str,
    version_id: str,
) -> dict:
    """Return deterministic stakeholder routing groups for a decision and version."""
    decision_node = _decision_node_id(decision_id)
    version_node = _version_node_id(version_id)

    _require_node(graph, decision_node, "Decision", decision_id)
    _require_node(graph, version_node, "Version", version_id)

    amplify = set()
    amplify |= _stakeholders_for_edge(graph, decision_node, "owns", {"Owner"})
    amplify |= _stakeholders_for_edge(graph, decision_node, "contributes", {"Contributor"})

    inform = set()
    inform |= _stakeholders_for_edge(graph, version_node, "informed_of", {"Informed"})
    inform |= _stakeholders_for_edge(graph, version_node, "affected_by", {"Affected"})

    linked_sources = set(source for source, _ in graph.in_edges(decision_node))
    linked_sources |= set(source for source, _ in graph.in_edges(version_node))

    restrict = set()
    for source in linked_sources:
        node_data = graph.nodes[source]
        if node_data.get("type") != "stakeholder":
            continue
        if node_data.get("role") != "Observer":
            continue
        stakeholder_id = node_data.get("stakeholder_id")
        if stakeholder_id:
            restrict.add(stakeholder_id)

    return {
        "amplify": sorted(amplify),
        "inform": sorted(inform),
        "restrict": sorted(restrict),
    }
