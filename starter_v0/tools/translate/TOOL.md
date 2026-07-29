---
name: translate
track: bonus
kind: local_formatter
inputs: [text, target_lang]
outputs: [translated_text]
side_effect: false
requires_confirmation: false
---

# Translate Tool

This tool translates a given text block into a target language.

## When to use
Use this tool when the user explicitly requests translation of a phrase, sentence, or article into another language (e.g. "Dịch đoạn văn này sang tiếng Anh").

## When NOT to use
Do NOT use this tool if the text content to translate is missing. In that case, call the `clarify` tool first.
