from sdd.schemas.rakso_core import ContextDeclaration

class InputGateEngine:
    """
    LAYER 1: INPUT GATE - CONTEXT DECLARATION LAYER
    Function: Prevent contamination between projects.
    """
    def __init__(self):
        self.active_context = None

    def declare_context(self, project_name: str) -> ContextDeclaration:
        """
        Validates and sets the current execution context.
        If empty, defaults to DEFAULT RAKSO.
        """
        context = ContextDeclaration(project_name=project_name)
        self.active_context = context.project_name
        return context

    def get_override_rules(self) -> dict:
        """
        LAYER 2: CONTEXT OVERRIDE ENGINE
        Applies project-specific execution rules based on active context.
        """
        if not self.active_context:
            raise ValueError("Context must be declared before getting override rules.")
            
        rules = {
            "allowed": [],
            "forbidden": [],
            "temporality": "PRESENT ONLY"
        }
        
        if self.active_context == "NORTHSTAR HUB":
            rules["allowed"] = [
                "Risk detection", "Error prevention", "Clinical framing", 
                "Forensic analysis", "Present-time containment", "Validation logic"
            ]
            rules["forbidden"] = [
                "Growth narratives", "Transformation", "Ladder ascension",
                "Aspirational language", "Coaching tone", "Future promises"
            ]
            
        return rules
