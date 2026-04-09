def build_classification_prompt(
    text: str,
    macro_labels: list[str],
    macro_to_micro: dict[str, list[str]],
    local_candidates: dict | None = None,
) -> str:
    macro_lines = "\n".join([f'- "{label}"' for label in macro_labels])

    mapping_lines = []
    for macro, micros in macro_to_micro.items():
        micro_str = ", ".join([f'"{micro}"' for micro in micros])
        mapping_lines.append(f'- "{macro}": [{micro_str}]')

    mapping_block = "\n".join(mapping_lines)

    support_block = ""
    if local_candidates:
        macro_candidates = local_candidates.get("macro_candidates", [])
        micro_candidates_by_macro = local_candidates.get("micro_candidates_by_macro", {})

        macro_candidate_lines = "\n".join(
            [f'- {item["label"]}: {item["confidence"]:.4f}' for item in macro_candidates]
        ) or "- nenhum"

        micro_candidate_lines = []
        for macro, items in micro_candidates_by_macro.items():
            formatted_items = ", ".join(
                [f'{item["label"]} ({item["confidence"]:.4f})' for item in items]
            )
            micro_candidate_lines.append(f'- {macro}: {formatted_items}')

        micro_block = "\n".join(micro_candidate_lines) or "- nenhum"

        support_block = (
            "Sinais auxiliares do classificador local (use apenas como apoio, sem copiar cegamente):\n"
            f"Top macros:\n{macro_candidate_lines}\n\n"
            f"Top micros por macro provável:\n{micro_block}"
        )

    return f'''
Você é um classificador de textos extremamente rigoroso.

Tarefa:
Classificar o texto em exatamente:
1. uma classe macro
2. uma classe micro compatível com a macro

Regras obrigatórias:
- Responda APENAS com um JSON válido.
- Não escreva markdown, comentários ou explicações fora do JSON.
- Preserve exatamente a grafia das classes fornecidas.
- A macro deve ser uma das opções permitidas.
- A micro deve pertencer à macro escolhida.
- Se o texto parecer ter duas intenções, escolha a categoria predominante no problema principal narrado.
- Em caso de ambiguidade, escolha a melhor classe permitida e marque is_ambiguous como true.
- Confianças devem ficar entre 0 e 1.

Classes macro permitidas:
{macro_lines}

Mapeamento de classes micro por macro:
{mapping_block}

{support_block}

Formato obrigatório:
{{
  "macro": "classe_macro_exata",
  "micro": "classe_micro_exata",
  "macro_confidence": 0.0,
  "micro_confidence": 0.0,
  "is_ambiguous": false,
  "justification": "frase curta e objetiva"
}}

Texto para classificar:
{text}
'''.strip()