import json
import re

class ThreatAnalyzer:
    def __init__(self, router):
        self.router = router

    async def analyze_event(self, event: dict) -> dict:
        """
        Full analysis pipeline for one threat event.
        Step 1: classify via Groq (gets severity, confidence, reason)
        Step 2: summarize via Cerebras (gets brief human explanation)
        Returns enriched event dict. Never raises — always returns dict.
        """
        event = dict(event)  # Don't mutate original

        # Step 1: Classify
        res = None
        try:
            res = await self.router.classify(event.get("payload", ""))
            raw_text = res.get("text", "").strip()

            # Strip markdown code fences if model disobeys instructions
            raw_text = re.sub(r"```(?:json)?", "", raw_text).strip()

            # Attempt JSON parse
            parsed = json.loads(raw_text)

            # Only update fields if parsed values are valid
            if isinstance(parsed.get("confidence"), (int, float)):
                event["confidence"] = round(float(parsed["confidence"]), 2)

            if parsed.get("severity") in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                event["severity"] = parsed["severity"]

            if isinstance(parsed.get("reason"), str):
                event["classify_reason"] = parsed["reason"][:120]

            event["provider_used"] = res.get("provider", "")
            event["analysis_latency_ms"] = res.get("latency_ms", 0)

        except json.JSONDecodeError:
            # Model returned non-JSON despite instructions — extract severity from text heuristically
            if res:
                text_lower = res.get("text", "").lower()
                if "critical" in text_lower:
                    event["severity"] = "CRITICAL"
                elif "high" in text_lower:
                    event["severity"] = "HIGH"
            event["classify_reason"] = "Classification parse failed — raw text used"

        except Exception:
            event["classify_reason"] = "Classification unavailable"

        # Step 2: Summarize
        try:
            res2 = await self.router.summarize(event)
            summary = res2.get("text", "").strip()
            if summary:
                event["ai_summary"] = summary
            else:
                event["ai_summary"] = "Summary not available."
        except Exception:
            event["ai_summary"] = "Summary unavailable."

        # Set final status based on severity
        if event["severity"] in ("CRITICAL", "HIGH"):
            event["status"] = "BLOCKED"
            event["mitigation"] = f"Agent {event['agent']} flagged — recommend isolation"
        else:
            event["status"] = "DETECTED"
            event["mitigation"] = "Monitoring — no immediate action required"

        return event

    async def get_security_advice(self, recent_events: list) -> str:
        """
        Send recent threat pattern to Gemini for 3 recommendations.
        Returns formatted string. Never raises.
        """
        if not recent_events:
            return "No recent threats detected. System appears stable."
        try:
            result = await self.router.advise(recent_events)
            text = result.get("text", "").strip()
            return text if text else "Advisory generation failed — all providers busy."
        except Exception as e:
            return f"Advisory unavailable: {str(e)[:60]}"
