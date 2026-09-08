class SummaryGenerator:
    @staticmethod
    def generate_summary(text: str) -> str:
        # Simple extractive summary stub
        lines = text.split('\n')
        summary_lines = [l for l in lines if len(l.split()) > 5][:5]
        return "Extracted Summary:\n" + "\n".join(summary_lines)

summary_generator = SummaryGenerator()
