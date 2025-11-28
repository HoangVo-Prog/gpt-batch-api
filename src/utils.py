import json
import pandas as pd

def read_prompt(path: str = "prompt.txt") -> str:
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    template = "".join(lines)

    # Nếu prompt gốc dùng kiểu ${statement} thì đổi về {statement}
    template = template.replace("${", "{")

    return template


def build_prompts_from_df(df: pd.DataFrame, PROMPT_TEMPLATE: str) -> list[str]:
    
    if not PROMPT_TEMPLATE:
        read_prompt()

    prompts: list[str] = []

    for _, row in df.iterrows():
        # Đảm bảo searchResults là chuỗi JSON
        sr = row.get("searchResults", "")
        if isinstance(sr, (dict, list)):
            sr_str = json.dumps(sr, ensure_ascii=False)
        else:
            sr_str = str(sr)

        prompt = PROMPT_TEMPLATE.format(
            statement=row.get("statement", ""),
            subject=row.get("subject", ""),
            speaker=row.get("speaker", ""),
            speakerJobTitle=row.get("speakerJobTitle", ""),
            stateInfo=row.get("stateInfo", ""),
            partyAffiliation=row.get("partyAffiliation", ""),
            barelyTrueCount=row.get("barelyTrueCount", ""),
            falseCount=row.get("falseCount", ""),
            halfTrueCount=row.get("halfTrueCount", ""),
            mostlyTrueCount=row.get("mostlyTrueCount", ""),
            pantsOnFireCount=row.get("pantsOnFireCount", ""),
            context=row.get("context", ""),
            searchResults=sr_str,
        )

        prompts.append(prompt)

    return prompts
