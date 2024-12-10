from base import IAgent

class Workspace:
    def __init__(self, agent: IAgent):
        self.agent = agent
        self.system_prompt = ""
        
        
    
    def run(self):
        self.agent.run()
    