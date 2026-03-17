"""Gradio UI for the Bioinformatics Literature Scout."""

import asyncio
import os
import traceback
from pathlib import Path
from datetime import datetime

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

# Debug: confirm env loaded
print(f"[DEBUG] OPENAI_API_KEY set: {bool(os.environ.get('OPENAI_API_KEY'))}")
print(f"[DEBUG] NCBI_EMAIL set: {os.environ.get('NCBI_EMAIL', 'NOT SET')}")

from src.scout_manager import run_pipeline

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


async def scout(query: str):
    """Run the pipeline and yield status updates to Gradio."""
    if not query.strip():
        yield "Please enter a research query."
        return

    print(f"[DEBUG] Starting pipeline for query: {query}")
    messages = []

    try:
        async for update in run_pipeline(query):
            print(f"[STATUS] {update[:80]}")
            messages.append(update)
            yield "\n\n".join(messages)

        # Save the brief to a file
        full_output = "\n\n".join(messages)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in query[:50]).strip()
        filename = OUTPUT_DIR / f"{timestamp}_{safe_name}.md"
        filename.write_text(full_output, encoding="utf-8")
        print(f"[DEBUG] Brief saved to {filename}")

    except Exception as e:
        error_msg = f"**Error:** {e}\n\n```\n{traceback.format_exc()}\n```"
        print(f"[ERROR] {e}")
        traceback.print_exc()
        yield error_msg


EXAMPLES = [
    "transformer models for single cell genomics 2023 2024",
    "single-cell ATAC-seq transfer learning",
    "graph neural networks protein structure prediction",
    "large language models biomedical text mining",
    "foundation models for genomics",
]

with gr.Blocks(title="Bioinformatics Literature Scout") as demo:
    gr.Markdown(
        "# Bioinformatics Literature Scout\n"
        "Enter a research topic and the multi-agent pipeline will search PubMed & ArXiv, "
        "then synthesize a structured research brief."
    )

    with gr.Row():
        query_input = gr.Textbox(
            label="Research Query",
            placeholder="e.g., transformer models for single cell genomics",
            lines=2,
            scale=4,
        )
        run_btn = gr.Button("Scout", variant="primary", scale=1)

    gr.Examples(examples=EXAMPLES, inputs=query_input)

    output = gr.Markdown(label="Research Brief")

    run_btn.click(fn=scout, inputs=query_input, outputs=output)
    query_input.submit(fn=scout, inputs=query_input, outputs=output)

demo.queue(max_size=5)

if __name__ == "__main__":
    demo.launch(max_threads=1, theme=gr.themes.Soft())
