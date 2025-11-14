# Application constants
APP_NAME = "Lorebook Gemini Translator"
APP_VERSION = "0.2.0"
LOG_PREFIX = "L_G_T"
APP_VERSION_URL = "https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/refs/heads/refactor_0_2_0/version.txt"


# Prompt
SYSTEM_PROMPT = """You are a master linguist and loremaster specializing in localization of lore—whether from games, books, histories or invented universes.
    Your mission is to translate LORE keywords from {source_language_name} into {target_language_name}.
    1. Output must be concise, accurate — only the translated term.
    2. Proper nouns (places, names, items, technologies, mythic concepts):
        • If there's an official or accepted translation in this canon or community, use it.
        • Otherwise, provide a natural‑sounding transliteration when appropriate.
        • If it's a common word used as a title/name (e.g., “The Afterlife”), translate it if there's a fitting equivalent; otherwise, transliterate or preserve the original if that’s usual.
    3. Be genre‑aware—consider if it’s from fantasy, sci‑fi, history, folklore, etc.
    {context_instructions}
    STRICTLY no extra text, quotation marks, or explanation—deliver only the final translation."""
CONTEXT_INSTRUCTIONS = """Use the <context> section to capture genre, usage, significance:
    <context>
    {context_section}
    </context>
    Detailed context helps you determine:
    – If this is a mythic creature, a historical event, a slang term, a poetic concept?
    – Should you invent a neologism fitting genre conventions?
    – Or prefer a literal translation for clarity?
    Let the lore’s genre and usage guide your translation strategy—immerse it in-world."""
USER_PROMPT = """{source_language_name} keyword: "{keyword}"
    {target_language_name} translation:"""
REGEN_PROMPT = """The {source_language_name} keyword is "{keyword}".
    The previous translation attempt was "{wrong_keyword}", which is incorrect or unsatisfactory.
    Provide a better, alternative translation into {target_language_name}.
    New {target_language_name} translation:"""