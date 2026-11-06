import json
import re
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "service-order-rag.md"
OUTPUT_FILE = BASE_DIR / "data" / "chunks.json"


# ============================================================
# HELPERS
# ============================================================

def slugify(text):
    """
    Convert heading text into a stable URL-like identifier.
    """

    text = text.lower().strip()

    text = re.sub(
        r"[*_`~]",
        "",
        text
    )

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text
    )

    text = re.sub(
        r"-+",
        "-",
        text
    )

    return text.strip("-")


def heading_level(line):
    """
    Return Markdown heading level.

    Example:

    # Heading       -> 1
    ## Heading      -> 2
    ### Heading     -> 3
    """

    match = re.match(
        r"^(#{1,6})\s+(.+?)\s*$",
        line
    )

    if not match:
        return None

    return len(match.group(1))


def heading_text(line):
    """
    Extract heading text from a Markdown heading.
    """

    match = re.match(
        r"^#{1,6}\s+(.+?)\s*$",
        line
    )

    if not match:
        return ""

    return match.group(1).strip()


# ============================================================
# PARSER
# ============================================================

def parse_markdown(file_path):
    """
    Parse Markdown into heading-based sections.

    Each section contains:

    - heading
    - heading_level
    - heading_path
    - content
    - text
    - source line range
    """

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        lines = file.readlines()

    headings = []

    for index, raw_line in enumerate(
        lines,
        start=1
    ):

        line = raw_line.rstrip("\n")

        level = heading_level(line)

        if level is not None:

            headings.append({
                "line": index,
                "level": level,
                "heading": heading_text(line)
            })

    chunks = []

    heading_stack = []

    for index, heading in enumerate(headings):

        start_line = heading["line"]

        if index + 1 < len(headings):

            end_line = (
                headings[index + 1]["line"] - 1
            )

        else:

            end_line = len(lines)

        # ----------------------------------------------------
        # Update heading hierarchy
        # ----------------------------------------------------

        while (
            heading_stack
            and heading_stack[-1]["level"]
            >= heading["level"]
        ):

            heading_stack.pop()

        heading_stack.append(
            heading
        )

        current_path = [
            item["heading"]
            for item in heading_stack
        ]

        # ----------------------------------------------------
        # Section content
        # ----------------------------------------------------

        section_lines = lines[
            start_line - 1:end_line
        ]

        # Remove the current heading from content.
        content_lines = section_lines[1:]

        content = "".join(
            content_lines
        ).strip()

        # ----------------------------------------------------
        # Skip empty sections
        # ----------------------------------------------------

        if not content:
            continue

        # ----------------------------------------------------
        # Build complete text
        # ----------------------------------------------------

        heading_prefix = "\n".join(
            "#" * item["level"]
            + " "
            + item["heading"]
            for item in heading_stack
        )

        text = (
            heading_prefix
            + "\n\n"
            + content
        ).strip()

        # ----------------------------------------------------
        # Stable chunk ID
        # ----------------------------------------------------

        chunk_id_parts = [
            slugify(item["heading"])
            for item in heading_stack
        ]

        chunk_id = "-".join(
            chunk_id_parts
        )

        chunks.append({

            "chunk_id":
                chunk_id,

            "document":
                file_path.name,

            "heading":
                heading["heading"],

            "heading_level":
                heading["level"],

            "heading_path":
                current_path,

            "content":
                content,

            "text":
                text,

            "start_line":
                start_line,

            "end_line":
                end_line
        })

    return headings, chunks


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("HEADING-BASED MARKDOWN CHUNKER")
    print("=" * 70)

    print()
    print("Input:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Markdown file not found:\n{INPUT_FILE}"
        )

    headings, chunks = parse_markdown(
        INPUT_FILE
    )

    print()
    print(
        f"Detected headings: {len(headings)}"
    )

    print(
        f"Created chunks: {len(chunks)}"
    )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("Saved to:")
    print(OUTPUT_FILE)

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CHUNK PREVIEW")
    print("=" * 70)

    for index, chunk in enumerate(
        chunks[:5],
        start=1
    ):

        print()
        print("-" * 70)

        print(
            f"Chunk #{index}"
        )

        print(
            f"ID: {chunk['chunk_id']}"
        )

        print(
            f"Heading: {chunk['heading']}"
        )

        print(
            "Heading Path: "
            + " > ".join(
                chunk["heading_path"]
            )
        )

        print(
            f"Source lines: "
            f"{chunk['start_line']}-"
            f"{chunk['end_line']}"
        )

        print()
        print("TEXT:")

        print(
            chunk["text"]
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()