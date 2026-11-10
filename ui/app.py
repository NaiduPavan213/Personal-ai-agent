import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import gradio as gr
from agents.supervisor import supervisor
from utils.email_confirmation import clear_pending, run_turn
from utils.voice import speak, transcribe


# ==================================================================== #
#  Theme
# ==================================================================== #

theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
).set(
    body_background_fill="#ffffff",
    block_background_fill="#ffffff",
    block_border_width="0px",
    block_radius="12px",
    block_shadow="none",
)


# ==================================================================== #
#  Backend functions
# ==================================================================== #

def ask_supervisor(messages):
    """Send the conversation to the Supervisor agent and return its reply."""
    response = supervisor.invoke({"messages": messages})
    return response["messages"][-1].content


def reply_audio(text, speak_replies):
    """Return a spoken version of the reply, or None if voice is off."""
    if not speak_replies:
        return None
    try:
        return speak(text)
    except Exception as error:
        # Speech is optional: never let it break the chat
        print(f"Text-to-speech failed: {error}")
        return None


def respond(message, history, speak_replies=False):
    """Send the user message to the Supervisor agent and append the reply."""
    if not message or not message.strip():
        return "", history, gr.update(), None

    history = history or []
    messages = history[-10:].copy()
    messages.append({"role": "user", "content": message})

    assistant_reply = run_turn(messages, ask_supervisor)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": assistant_reply})

    # Hide the welcome panel once the conversation has started
    return (
        "",
        history,
        gr.update(visible=False),
        reply_audio(assistant_reply, speak_replies),
    )


def voice_respond(audio_path, history, speak_replies):
    """Transcribe a voice message, then handle it like a typed one."""
    if not audio_path:
        return None, history, gr.update(), None

    try:
        message = transcribe(audio_path)
    except Exception as error:
        history = (history or []) + [{
            "role": "assistant",
            "content": f"❌ Sorry, I couldn't transcribe that: {error}",
        }]
        return None, history, gr.update(visible=False), None

    if not message:
        history = (history or []) + [{
            "role": "assistant",
            "content": "🎤 I didn't catch that. Please try again.",
        }]
        return None, history, gr.update(visible=False), None

    _, history, panel, audio = respond(message, history, speak_replies)

    # Clear the recorder so it's ready for the next message
    return None, history, panel, audio


def clear_chat():
    """Reset the conversation and bring back the welcome panel."""
    clear_pending()
    return [], gr.update(visible=True), None


def open_calendar():
    webbrowser.open_new_tab("https://calendar.google.com/")


def open_gmail():
    webbrowser.open_new_tab("https://mail.google.com/")


def use_example(example_text):
    return example_text


# ==================================================================== #
#  CSS  (ChatGPT-style: dark sidebar + light chat surface)
# ==================================================================== #

custom_css = """
:root{
    --sidebar-bg:#171a21;
    --sidebar-bg-hover:#242832;
    --sidebar-border:#2a2e37;
    --sidebar-text:#e6e8ee;
    --sidebar-text-dim:#9099ab;
    --accent:#3b82f6;
    --accent-soft:#eaf1ff;
    --surface:#ffffff;
    --surface-alt:#f7f8fa;
    --border:#e7e9ee;
    --text-main:#1f2430;
    --text-dim:#6b7280;
    --radius-lg:16px;
    --radius-md:12px;
}

* { font-family:"Inter","Segoe UI",sans-serif; }

html, body{
    height:100%;
    margin:0;
    padding:0;
}

body, .gradio-container{
    background:var(--surface-alt) !important;
}

.gradio-container{
    max-width:100% !important;
    width:100% !important;
    min-height:100vh !important;
    margin:0 !important;
    padding:16px !important;
    box-sizing:border-box !important;
}

footer{ display:none !important; }
.gr-prose h1, .gr-prose h2{ margin:0; }

/* ---------------------------------------------------------------- */
/* Header                                                            */
/* ---------------------------------------------------------------- */
.app-header{
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:var(--radius-lg);
    padding:16px 24px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    box-shadow:0 2px 10px rgba(20,20,40,.04);
    margin-bottom:16px;
}

.app-header h1{
    font-size:20px;
    font-weight:700;
    color:var(--text-main);
    margin:0;
}

.app-header p{
    font-size:13px;
    color:var(--text-dim);
    margin:2px 0 0 0;
}

.status-pill{
    display:inline-flex;
    align-items:center;
    gap:6px;
    background:#ecfdf3;
    color:#15803d;
    font-size:12px;
    font-weight:600;
    padding:6px 12px;
    border-radius:999px;
    border:1px solid #bbf7d0;
}

.status-pill .dot{
    width:7px;
    height:7px;
    border-radius:50%;
    background:#22c55e;
}

/* ---------------------------------------------------------------- */
/* Sidebar (dark, ChatGPT-style)                                     */
/* ---------------------------------------------------------------- */
.main-row{
    align-items:stretch !important;
}

.sidebar{
    background:var(--sidebar-bg);
    border-radius:var(--radius-lg);
    padding:18px 14px;
    height:100%;
    min-height:calc(100vh - 150px);
    display:flex;
    flex-direction:column;
    box-sizing:border-box;
}

.sidebar-brand{
    display:flex;
    align-items:center;
    gap:10px;
    padding:4px 6px 18px 6px;
    border-bottom:1px solid var(--sidebar-border);
    margin-bottom:16px;
}

.sidebar-brand .logo{
    font-size:22px;
}

.sidebar-brand .title{
    color:var(--sidebar-text);
    font-weight:700;
    font-size:15px;
}

.sidebar-brand .subtitle{
    color:var(--sidebar-text-dim);
    font-size:11px;
}

.sidebar #new-chat-btn{
    background:var(--accent) !important;
    color:#fff !important;
    border:none !important;
    font-weight:600 !important;
    border-radius:var(--radius-md) !important;
    padding:10px 14px !important;
    text-align:left !important;
    box-shadow:none !important;
}

.sidebar #new-chat-btn:hover{
    background:#2f6fe0 !important;
}

.sidebar-section-label{
    color:var(--sidebar-text-dim);
    font-size:11px;
    font-weight:700;
    letter-spacing:.06em;
    text-transform:uppercase;
    margin:18px 6px 8px 6px;
}

.sidebar .nav-btn{
    background:transparent !important;
    color:var(--sidebar-text) !important;
    border:1px solid transparent !important;
    justify-content:flex-start !important;
    text-align:left !important;
    font-size:14px !important;
    font-weight:500 !important;
    padding:9px 12px !important;
    box-shadow:none !important;
}

.sidebar .nav-btn:hover{
    background:var(--sidebar-bg-hover) !important;
    border-color:var(--sidebar-border) !important;
}

.sidebar .service-row{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:8px 10px;
    border-radius:var(--radius-md);
    color:var(--sidebar-text-dim);
}

.sidebar-footer{
    margin-top:auto;
    padding-top:14px;
    border-top:1px solid var(--sidebar-border);
}

.sidebar .nav-btn.settings-btn{
    color:var(--sidebar-text-dim) !important;
}

/* ---------------------------------------------------------------- */
/* Chat area                                                         */
/* ---------------------------------------------------------------- */
.chat-area{
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:var(--radius-lg);
    padding:12px;
    box-shadow:0 2px 10px rgba(20,20,40,.04);
    display:flex;
    flex-direction:column;
    height:100%;
    min-height:calc(100vh - 150px);
    box-sizing:border-box;
}

/* Let the chatbot itself stretch to fill leftover space in the chat-area,
   so its bottom edge lines up with the sidebar's bottom edge */
.chat-area .bubble-wrap,
.chat-area > div:has(> .chatbot),
.chat-area [data-testid="chatbot"]{
    flex:1 1 auto !important;
}

/* Welcome panel shown before the first message */
.welcome-panel{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:60px 20px;
}

.welcome-panel .emoji{
    font-size:44px;
    margin-bottom:10px;
}

.welcome-panel h2{
    font-size:22px;
    font-weight:700;
    color:var(--text-main);
    margin:0 0 6px 0;
}

.welcome-panel p{
    color:var(--text-dim);
    font-size:14px;
    max-width:420px;
    margin:0 auto 18px auto;
}

.welcome-panel .example-btn{
    background:var(--surface-alt) !important;
    color:var(--text-main) !important;
    border:1px solid var(--border) !important;
    border-radius:var(--radius-md) !important;
    font-size:13px !important;
    box-shadow:none !important;
}

.welcome-panel .example-btn:hover{
    background:var(--accent-soft) !important;
    border-color:#bfdbfe !important;
}

/* Input row */
.input-row{
    border-top:1px solid var(--border);
    padding-top:10px;
    margin-top:6px;
}

.voice-row{
    margin-top:8px;
    gap:10px;
}

textarea{
    border-radius:var(--radius-md) !important;
    border:1px solid var(--border) !important;
}

#send-btn{
    background:var(--accent) !important;
    border:none !important;
    color:#fff !important;
    font-weight:600 !important;
    border-radius:var(--radius-md) !important;
}

#send-btn:hover{
    background:#2f6fe0 !important;
}

button{
    border-radius:var(--radius-md) !important;
}
"""


# ==================================================================== #
#  UI
# ==================================================================== #

with gr.Blocks(
    title="Personal AI Assistant",
) as demo:

    # ---------------- Header ---------------- #
    with gr.Row(elem_classes="app-header"):
        with gr.Column(scale=6, min_width=0):
            gr.Markdown(
                "<h1>🤖 Personal AI Assistant</h1>"
                "<p>Your intelligent assistant for Gmail, Calendar, and future AI tools</p>"
            )
        with gr.Column(scale=1, min_width=160):
            gr.Markdown(
                '<div style="display:flex;justify-content:flex-end;">'
                '<span class="status-pill"><span class="dot"></span>Supervisor online</span>'
                '</div>'
            )

    with gr.Row(equal_height=True, elem_classes="main-row"):

        # ---------------- Sidebar ---------------- #
        with gr.Column(scale=1, min_width=250):
            with gr.Column(elem_classes="sidebar"):

                gr.Markdown(
                    '<div class="sidebar-brand">'
                    '<span class="logo">🤖</span>'
                    '<div><div class="title">AI Assistant</div>'
                    '<div class="subtitle">Personal workspace</div></div>'
                    '</div>'
                )

                new_chat = gr.Button(
                    "＋  New Chat",
                    elem_id="new-chat-btn",
                )

                gr.Markdown('<div class="sidebar-section-label">Connected Services</div>')

                gmail = gr.Button("📧  Gmail", elem_classes="nav-btn")
                calendar = gr.Button("📅  Calendar", elem_classes="nav-btn")

                gr.Markdown('<div class="sidebar-section-label">Workspace</div>')

                settings = gr.Button("⚙️  Settings", elem_classes="nav-btn settings-btn")

                with gr.Column(elem_classes="sidebar-footer"):
                    gr.Markdown(
                        '<div class="service-row">'
                        '<span>🟢 Gmail connected</span></div>'
                        '<div class="service-row">'
                        '<span>🟢 Calendar connected</span></div>'
                    )

        # ---------------- Main chat ---------------- #
        with gr.Column(scale=4):
            with gr.Column(elem_classes="chat-area"):

                # Welcome panel (visible until the first message is sent)
                with gr.Column(elem_classes="welcome-panel", visible=True) as welcome_panel:
                    gr.Markdown(
                        '<div class="emoji">👋</div>'
                        '<h2>How can I help you today?</h2>'
                        '<p>Ask me to check your inbox, manage your calendar, '
                        'or anything else — I\u2019ll route it to the right tool.</p>'
                    )
                    with gr.Row():
                        ex1 = gr.Button("📧 Summarize my unread emails", elem_classes="example-btn")
                        ex2 = gr.Button("📅 What's on my calendar today?", elem_classes="example-btn")
                    with gr.Row():
                        ex3 = gr.Button("✍️ Draft a follow-up email", elem_classes="example-btn")
                        ex4 = gr.Button("🗓️ Schedule a meeting for tomorrow", elem_classes="example-btn")

                chatbot = gr.Chatbot(
                    height="100%",
                    layout="bubble",
                    show_label=False,
                    avatar_images=(None, None),
                    elem_classes="main-chatbot",
                )

                with gr.Row(elem_classes="input-row"):
                    textbox = gr.Textbox(
                        placeholder="Message your assistant...",
                        scale=8,
                        show_label=False,
                        container=False,
                    )
                    send = gr.Button("Send", elem_id="send-btn", scale=1)

                # ---------------- Voice ---------------- #
                with gr.Row(elem_classes="voice-row", equal_height=True):
                    mic = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="🎤 Voice message",
                        scale=3,
                    )
                    with gr.Column(scale=2, min_width=200):
                        speak_replies = gr.Checkbox(
                            label="🔊 Speak replies aloud",
                            value=True,
                        )
                        spoken_reply = gr.Audio(
                            label="Last reply",
                            autoplay=True,
                            interactive=False,
                        )

    # ==================================================================== #
    #  Events
    # ==================================================================== #

    send.click(
        fn=respond,
        inputs=[textbox, chatbot, speak_replies],
        outputs=[textbox, chatbot, welcome_panel, spoken_reply],
    )

    textbox.submit(
        fn=respond,
        inputs=[textbox, chatbot, speak_replies],
        outputs=[textbox, chatbot, welcome_panel, spoken_reply],
    )

    mic.stop_recording(
        fn=voice_respond,
        inputs=[mic, chatbot, speak_replies],
        outputs=[mic, chatbot, welcome_panel, spoken_reply],
    )

    new_chat.click(
        fn=clear_chat,
        outputs=[chatbot, welcome_panel, spoken_reply],
    )

    for ex_btn in (ex1, ex2, ex3, ex4):
        ex_btn.click(fn=use_example, inputs=ex_btn, outputs=textbox)

    calendar.click(fn=open_calendar, inputs=[], outputs=[])
    gmail.click(fn=open_gmail, inputs=[], outputs=[])


if __name__ == "__main__":
    demo.launch(theme=theme, css=custom_css)
