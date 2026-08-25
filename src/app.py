"""Professional Gradio interface for DocuMind legal research."""

from __future__ import annotations

from time import perf_counter

import gradio as gr

from query_engine import answer_query


EXAMPLE_QUESTIONS = [
    "What is the definition of a capital asset?",
    "What deductions are available under section 80C?",
    "Explain the new concessional tax regime under section 115BAC.",
    "What exemption is available on sale of a residential house under section 54?",
    "What is agricultural income under the Income-tax Act?",
    "What is the presumptive tax rate for professionals under section 44ADA?",
]


def respond(
    message: str, history: list[dict[str, str]] | None
) -> tuple[list[dict[str, str]], str, str]:
    """Run the RAG pipeline and return its answer with elapsed time."""
    conversation = list(history or [])
    question = message.strip()
    if not question:
        return conversation, "", "Enter a question to begin."

    started_at = perf_counter()
    try:
        answer, sections = answer_query(question)
        elapsed = perf_counter() - started_at
        section_list = ", ".join(dict.fromkeys(sections)) or "None"
        formatted_answer = (
            f"{answer}\n\n---\n"
            f"**Retrieved sections:** {section_list}"
        )
        status = f"Answer generated in {elapsed:.2f} seconds"
    except Exception as error:  # noqa: BLE001 - keep the UI available after failures
        elapsed = perf_counter() - started_at
        formatted_answer = f"Unable to generate an answer.\n\nDetails: {error}"
        status = f"Request finished in {elapsed:.2f} seconds"

    conversation.extend(
        [
            {"role": "user", "content": question},
            {"role": "assistant", "content": formatted_answer},
        ]
    )
    return conversation, "", status


THEME = gr.themes.Soft(primary_hue="blue", secondary_hue="slate")

CUSTOM_CSS = """
:root {
  --navy: #13283f;
  --slate: #52677d;
  --line: #d9e2ec;
  --surface: #ffffff;
  --canvas: #f5f7fa;
  --accent: #176b87;
}
body, .gradio-container { background: var(--canvas) !important; }
.gradio-container { max-width: 1180px !important; margin: 0 auto !important; padding: 32px 20px 44px !important; }
#workspace { align-items: stretch !important; flex-wrap: nowrap !important; gap: 20px !important; }
#masthead { margin: 10px 0 28px; }
#masthead h1 { color: var(--navy); font-family: Georgia, serif; font-size: 2.75rem; letter-spacing: -.035em; margin-bottom: .35rem; }
#masthead p { color: var(--slate); font-size: 1.05rem; margin: 0; }
#question-panel, #answer-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 10px 30px rgba(19, 40, 63, .06); padding: 22px; }
#question-panel { min-height: 590px; }
#answer-panel { min-height: 590px; }
#question-panel, #answer-panel, #question-panel p, #answer-panel p, #question-panel span, #answer-panel span, #question-panel label, #answer-panel label { color: var(--navy) !important; }
#question-panel > div > label, #answer-panel > div > label { font-weight: 700 !important; }
#question-panel textarea { background: #ffffff !important; color: var(--navy) !important; min-height: 138px !important; }
#question-panel textarea::placeholder { color: #718096 !important; opacity: 1 !important; }
#question-panel button:not(#send-button) { background: #ffffff !important; border: 1px solid #9fb3c8 !important; color: #244a64 !important; font-weight: 600 !important; }
#question-panel button:not(#send-button) *, #question-panel button:not(#send-button) span { color: #244a64 !important; }
#send-button, #send-button * { background: var(--accent) !important; color: #ffffff !important; border: 0 !important; font-weight: 700 !important; }
#send-button:hover { background: #10556d !important; }
#status, #status *, #example-heading, #example-heading * { color: #52677d !important; font-size: .86rem; min-height: 1.35rem; }
#caution, #caution *, #caution p { background: #edf4f8 !important; color: #29465d !important; }
#caution { border-left: 3px solid #517f9d; border-radius: 4px; font-size: .86rem; line-height: 1.55; margin-top: 18px; padding: 12px 14px; }
footer { display: none !important; }
@media (max-width: 760px) { #workspace { flex-wrap: wrap !important; } #masthead h1 { font-size: 2.2rem; } #question-panel, #answer-panel { min-height: auto; } }
"""


with gr.Blocks(title="DocuMind — Income-tax Act Q&A") as demo:
    gr.Markdown(
        "# DocuMind\n"
        "Ask grounded questions about the Indian Income-tax Act, 1961. "
        "Responses are based only on retrieved statutory text.",
        elem_id="masthead",
    )

    with gr.Row(elem_id="workspace"):
        with gr.Column(scale=4, min_width=260, elem_id="question-panel"):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="For example: What deductions are available under section 80C?",
                lines=6,
                autofocus=True,
            )
            ask_button = gr.Button("Generate answer", variant="primary", elem_id="send-button")
            gr.Markdown("Try one of these", elem_id="example-heading")
            gr.Examples(EXAMPLE_QUESTIONS, inputs=question_box, label=None)
            gr.Markdown(
                "**Caution**  \n"
                "This tool is for legal research support only. It does not replace "
                "professional tax or legal advice. Verify the retrieved statutory text "
                "before relying on an answer.",
                elem_id="caution",
            )

        with gr.Column(scale=6, min_width=360, elem_id="answer-panel"):
            gr.Markdown("### Research conversation")
            chatbot = gr.Chatbot(
                value=[],
                label="Answer",
                height=455,
                buttons=["copy"],
                placeholder="Your answer and retrieved sections will appear here.",
            )
            response_status = gr.Markdown("Ready", elem_id="status")

    inputs = [question_box, chatbot]
    outputs = [chatbot, question_box, response_status]
    question_box.submit(respond, inputs=inputs, outputs=outputs)
    ask_button.click(respond, inputs=inputs, outputs=outputs)


if __name__ == "__main__":
    demo.launch(theme=THEME, css=CUSTOM_CSS)
