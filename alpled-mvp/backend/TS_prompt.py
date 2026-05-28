SYSTEM_PROMPT = """
반드시 JSON만 출력하세요. 당신은 CBD SW개발 표준 산출물 가이드(D10)에 따라 통합시험 시나리오를 생성하는 전문가입니다.
출력 JSON은 반드시 {"scenarios": [...], "cases": [...]} 구조를 따릅니다.
cases의 각 행은 test_procedure 1개에 1:1 대응되어야 하며 test_result는 항상 null입니다.
"""

FEW_SHOT_INPUT = "{}"
FEW_SHOT_OUTPUT = "{}"

def build_prompt(requirement: dict, ui_data: dict | None = None) -> list:
    import json
    user_payload = {
        "requirement": requirement,
        "ui_screens": (ui_data or {}).get("ui_screens", (ui_data or {}).get("screens", [])),
        "instruction": "입력 요구사항과 UI 설계서를 기반으로 D10 통합시험 시나리오 JSON만 생성하세요."
    }
    return [{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}]
