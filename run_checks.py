# Прогон контрольных сценариев без браузера (урок 34)
# Запуск из папки ai-course: python final_project/run_checks.py
import json
import os
from pathlib import Path

from agent_core import build_agent, run_agent
from tickets_store import load_tickets

CASES_FILE = Path(__file__).parent / "eval_cases.json"
NAMES = {"anna": "Анна", "boris": "Борис"}


def check_case(agent, case):
    """Возвращает список причин провала. Пустой список — сценарий пройден."""
    if case.get("tools_down"):
        os.environ["TOOLS_DOWN"] = "1"
    before = len(load_tickets())
    try:
        report = run_agent(agent, [{"role": "user", "content": case["question"]}],
                           case["user"], NAMES[case["user"]])
    finally:
        os.environ.pop("TOOLS_DOWN", None)

    problems = []
    used = sorted(set(report["tools"]))
    if used != sorted(case["expect_tools"]):
        problems.append(f"инструменты {used}, ожидались {case['expect_tools']}")
    sources = [s["source"] for s in report["sources"]]
    if "expect_source" in case and case["expect_source"] not in sources:
        problems.append(f"нет источника {case['expect_source']}")
    answer = (report["error"] or report["answer"]).lower()
    if "must_say" in case and case["must_say"] not in answer:
        problems.append(f"в ответе нет «{case['must_say']}»")
    if "must_not_say" in case and case["must_not_say"] in answer:
        problems.append(f"в ответе есть «{case['must_not_say']}»")
    if case.get("expect_draft") and report["draft"] is None:
        problems.append("нет черновика заявки")
    if case.get("no_write") and len(load_tickets()) != before:
        problems.append("заявка записана без подтверждения")
    return problems


def main():
    with open(CASES_FILE, encoding="utf-8") as file:
        cases = json.load(file)
    agent = build_agent()
    passed = 0
    for case in cases:
        problems = check_case(agent, case)
        if problems:
            print(f"✗ {case['id']}: {'; '.join(problems)}")
        else:
            passed += 1
            print(f"✓ {case['id']}")
    print(f"Пройдено: {passed} из {len(cases)}")


if __name__ == "__main__":
    main()
