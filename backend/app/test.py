from backend.app.core.decision_graph import init_graph
from backend.app.agents.briefing_agent import ProjectBriefingAgent


g = init_graph()
# populate mock decisions + versions here

agent = ProjectBriefingAgent()
brief = agent.generate_brief(g, "proj-1")

print(brief["brief_text"])
