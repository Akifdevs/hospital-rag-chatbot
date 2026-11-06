import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "chunks.json"
OUTPUT_FILE = BASE_DIR / "data" / "embedded_chunks.json"


# =========================================================
# Configuration
# =========================================================

MODEL_NAME = "BAAI/bge-small-en-v1.5"


# =========================================================
# Load chunks
# =========================================================

def load_chunks():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Chunks file not found:\n{INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# =========================================================
# Build embedding text
# =========================================================

def build_embedding_text(chunk):
    """
    Build the exact text that will be embedded.

    The content comes directly from chunk["content"].
    """

    heading_lines = []

    for level, heading in enumerate(
        chunk["heading_path"],
        start=1
    ):
        heading_lines.append(
            f"{'#' * level} {heading}"
        )

    heading_context = "\n".join(
        heading_lines
    )

    content = chunk["content"].strip()

    if content:
        return (
            f"{heading_context}\n\n"
            f"{content}"
        )

    return heading_context


# =========================================================
# Main
# =========================================================

def main():

    print("=" * 60)
    print("EMBEDDING PIPELINE")
    print("=" * 60)

    # -----------------------------------------------------
    # Load chunks
    # -----------------------------------------------------

    chunks = load_chunks()

    print(
        f"\nLoaded {len(chunks)} chunks."
    )

    # -----------------------------------------------------
    # Build embedding texts
    # -----------------------------------------------------

    texts = []

    for chunk in chunks:

        text = build_embedding_text(
            chunk
        )

        texts.append(text)

    # -----------------------------------------------------
    # Verify BEFORE embedding
    # -----------------------------------------------------

    print("\nFirst chunk that will be embedded:")
    print("-" * 60)
    print(texts[0])
    print("-" * 60)

    # -----------------------------------------------------
    # Load model
    # -----------------------------------------------------

    print(
        f"\nLoading model:\n{MODEL_NAME}"
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    print("Model loaded.")

    # -----------------------------------------------------
    # Generate embeddings
    # -----------------------------------------------------

    print("\nGenerating embeddings...")

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    print(
        "\nEmbedding generation complete."
    )

    print(
        f"Number of embeddings: "
        f"{len(embeddings)}"
    )

    print(
        f"Embedding dimension: "
        f"{embeddings.shape[1]}"
    )

    # -----------------------------------------------------
    # Create output
    # -----------------------------------------------------

    embedded_chunks = []

    for chunk, text, embedding in zip(
        chunks,
        texts,
        embeddings
    ):

        embedded_chunk = chunk.copy()

        # IMPORTANT:
        # Replace text with the exact text
        # that was actually embedded.
        embedded_chunk["text"] = text

        embedded_chunk["embedding"] = (
            embedding.tolist()
        )

        embedded_chunks.append(
            embedded_chunk
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            embedded_chunks,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )

    # -----------------------------------------------------
    # Verify output
    # -----------------------------------------------------

    with OUTPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        saved_chunks = json.load(file)

    print("\nVerifying saved data...")

    print("-" * 60)

    print(
        saved_chunks[0]["text"]
    )

    print("-" * 60)

    print(
        f"\nEmbedding dimension: "
        f"{len(saved_chunks[0]['embedding'])}"
    )

    print("\nVerification successful.")


if __name__ == "__main__":
    main()