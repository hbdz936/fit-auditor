from models.schemas import LineBlock


def parse_resume(text: str) -> list[LineBlock]:
    """Line-index the resume so the auditor can cite exact lines as
    evidence, and the verifier can check those citations against real
    text instead of trusting the model's word for it."""
    blocks: list[LineBlock] = []
    counter = 1
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        blocks.append(LineBlock(id=f"L{counter:03d}", text=line))
        counter += 1
    return blocks