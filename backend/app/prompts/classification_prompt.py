def build_classification_prompt(
    text: str,
    macro_labels: list[str],
    macro_to_detail: dict[str, list[str]],
) -> str:
    macro_lines = "\n".join([f'- "{label}"' for label in macro_labels])

    mapping_lines = []
    for macro, details in macro_to_detail.items():
        detail_str = ", ".join([f'"{detail}"' for detail in details])
        mapping_lines.append(f'- "{macro}": [{detail_str}]')

    mapping_block = "\n".join(mapping_lines)

    return f"""
Você é um classificador de textos extremamente rigoroso.

Tarefa:
Classificar o texto em exatamente:
1. uma classe macro
2. uma classe detail compatível com a macro

Regras obrigatórias:
- Responda APENAS com um JSON válido.
- Não escreva markdown, comentários ou explicações fora do JSON.
- Preserve exatamente a grafia das classes fornecidas.
- A macro deve ser uma das opções permitidas.
- A detail deve pertencer à macro escolhida.
- Confianças devem ficar entre 0 e 1.

Classes macro permitidas:
{macro_lines}

Mapeamento de classes detail por macro:
{mapping_block}

Formato obrigatório:
{{
  "macro": "classe_macro_exata",
  "detail": "classe_detail_exata",
  "macro_confidence": 0.0,
  "detail_confidence": 0.0
}}

Texto para classificar:
{text}
""".strip()