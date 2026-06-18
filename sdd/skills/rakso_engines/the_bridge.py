from sdd.schemas.rakso_core import ComplianceDecision, OutputStatus, StrategyOutput

class TheBridgeEngine:
    """
    LAYER 5: THE BRIDGE - COMPLIANCE & SEMANTIC JUDGE
    Role: Absolute authority layer. Judge ALL outputs.
    """
    
    PROHIBITED_CONCEPTS = [
        "guarantee", "promise", "100%", "fix your life", 
        "achieve your dreams", "success path", "financial freedom"
    ]

    def evaluate_output(self, strategy: StrategyOutput, active_context: str = None) -> ComplianceDecision:
        """
        Judges the strategy output. Can APPROVE, CORRECT (CONDITIONAL), or BLOCK.
        """
        violations = []
        content_lower = strategy.content.lower()

        # Check prohibited concepts
        for concept in self.PROHIBITED_CONCEPTS:
            if concept in content_lower:
                violations.append(f"Contains prohibited hype concept: '{concept}'")

        # Check Context Override Rules (e.g. Northstar Hub)
        if active_context == "NORTHSTAR HUB":
            northstar_forbidden = [
                "growth", "journey", "transformation", "ascension"
            ]
            for concept in northstar_forbidden:
                if concept in content_lower:
                    violations.append(f"Context 'NORTHSTAR HUB' forbidden concept used: '{concept}'")

        # Check shame language or aspiration drift
        if "you should feel bad" in content_lower or "shame on you" in content_lower:
            violations.append("Shame language detected. Dignity overrides conversion.")

        if violations:
            # Determine if it's a hard block or conditional
            if len(violations) >= 2 or any("guarantee" in v for v in violations):
                return ComplianceDecision(
                    status=OutputStatus.BLOCKED,
                    violations_detected=violations,
                    rejection_reason="Multiple violations or hard hype guarantees detected. EXECUTION STOPS."
                )
            else:
                return ComplianceDecision(
                    status=OutputStatus.CONDITIONAL,
                    violations_detected=violations,
                    rejection_reason="Minor violations detected. Needs semantic correction."
                )

        return ComplianceDecision(status=OutputStatus.APPROVED)
