import base64
import os
import sys
import tempfile
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import gradio as gr
from agents.image_agent import content_to_text
from agents.supervisor import supervisor
from utils.attachments import check_image, clear_image, set_image
from utils.email_confirmation import clear_pending, run_turn
from utils.voice import transcribe


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
    return content_to_text(response["messages"][-1].content)


def _image_note(name):
    return f"[Image attached: {name}]"


def to_llm_messages(history):
    """
    Convert chat history into plain-text messages for the language models.

    The chat stores images as file blocks; the models only need to know
    an image was attached (the image itself is kept in utils.attachments).
    """
    messages = []
    for message in history:
        content = message["content"]
        blocks = content if isinstance(content, list) else [content]
        parts = []
        for block in blocks:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, dict):
                file = block.get("file", block)
                name = file.get("orig_name") or Path(file.get("path", "")).name
                parts.append(_image_note(name))
        text = "\n".join(part for part in parts if part)
        if text:
            messages.append({"role": message["role"], "content": text})
    return messages


def respond(message, history, pending_image=None):
    """Send the user message (and any attached image) to the Supervisor."""
    message = (message or "").strip()
    no_change = ("", history, gr.update(), pending_image, gr.update())

    if not message and not pending_image:
        return no_change

    history = history or []
    messages = to_llm_messages(history[-10:])
    new_turn = []

    if pending_image:
        try:
            image = set_image(pending_image)
        except ValueError as error:
            gr.Warning(str(error))
            return (message, history, gr.update(), None, gr.update(visible=False))

        message = message or "Describe this image."
        messages.append({
            "role": "user",
            "content": f"{_image_note(image.name)}\n{message}",
        })
        new_turn.append({"role": "user", "content": {"path": image.path}})
    else:
        messages.append({"role": "user", "content": message})

    assistant_reply = run_turn(messages, ask_supervisor)

    history.extend(new_turn)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": assistant_reply})

    # Clear the box and the attachment preview; hide the welcome panel
    return "", history, gr.update(visible=False), None, gr.update(visible=False)


def attach_image(path):
    """Show a preview of the image chosen with the 📎 button."""
    try:
        check_image(path)
    except ValueError as error:
        gr.Warning(str(error))
        return None, gr.update(visible=False), gr.update()
    return path, gr.update(visible=True), path


def remove_attachment():
    return None, gr.update(visible=False), None


def dictate(text, audio_data):
    """
    Turn a recording from the mic button into text in the message box.

    `audio_data` is filled in by the browser (see MIC_JS): empty when
    recording starts, a base64 data URL when it stops, or "ERROR:..." if
    the microphone could not be used.
    """
    if not audio_data:
        return gr.update(), ""

    if audio_data.startswith("ERROR:"):
        gr.Warning(f"Microphone not available: {audio_data[6:]}")
        return gr.update(), ""

    header, encoded = audio_data.split(",", 1)
    extension = next(
        (ext for ext in ("ogg", "mp4", "wav") if ext in header), "webm"
    )

    fd, path = tempfile.mkstemp(suffix=f".{extension}")
    try:
        with os.fdopen(fd, "wb") as audio_file:
            audio_file.write(base64.b64decode(encoded))
        heard = transcribe(path)
    except Exception as error:
        gr.Warning(f"Couldn't transcribe that: {error}")
        return gr.update(), ""
    finally:
        os.remove(path)

    if not heard:
        gr.Info("I didn't catch that. Please try again.")
        return gr.update(), ""

    # Add to whatever is already typed, so you can edit before sending
    text = (text or "").rstrip()
    return (f"{text} {heard}" if text else heard), ""


def clear_chat():
    """Reset the conversation and bring back the welcome panel."""
    clear_pending()
    clear_image()
    return [], gr.update(visible=True), None, gr.update(visible=False)


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

/* Mic button inside the message box */
.input-box{
    position:relative !important;
}

.input-box textarea{
    padding-right:48px !important;
    padding-left:46px !important;
}

/* 📎 attach button inside the message box (left side) */
#attach-btn{
    --clip-icon:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48'/%3E%3C/svg%3E");
    position:absolute !important;
    left:8px;
    top:50%;
    transform:translateY(-50%);
    z-index:5;
    width:34px !important;
    min-width:34px !important;
    max-width:34px !important;
    height:34px !important;
    padding:0 !important;
    border:none !important;
    border-radius:50% !important;
    background:transparent !important;
    box-shadow:none !important;
    color:var(--text-dim) !important;
    font-size:0 !important;
}

#attach-btn::before{
    content:"";
    display:block;
    width:18px;
    height:18px;
    margin:auto;
    background-color:currentColor;
    -webkit-mask:var(--clip-icon) center / contain no-repeat;
    mask:var(--clip-icon) center / contain no-repeat;
}

#attach-btn:hover{
    background:var(--surface-alt) !important;
    color:var(--text-main) !important;
}

/* Thumbnail of the image waiting to be sent */
.attach-preview{
    position:relative;
    width:72px !important;
    max-width:72px !important;
    margin:4px 0 0 4px;
    flex:0 0 auto !important;
}

#attach-thumb{
    width:64px !important;
    height:64px !important;
    border-radius:10px !important;
    overflow:hidden;
    border:1px solid var(--border) !important;
}

#attach-thumb img{
    width:64px !important;
    height:64px !important;
    object-fit:cover !important;
}

#attach-remove{
    position:absolute !important;
    top:-6px;
    right:0;
    z-index:6;
    width:20px !important;
    min-width:20px !important;
    max-width:20px !important;
    height:20px !important;
    padding:0 !important;
    border-radius:50% !important;
    background:var(--text-main) !important;
    color:#fff !important;
    font-size:11px !important;
    line-height:20px !important;
    border:none !important;
    box-shadow:none !important;
}

/* Images inside chat bubbles */
.main-chatbot img{
    max-width:260px !important;
    max-height:260px !important;
    border-radius:10px !important;
}

/* No Gradio loading bar/timer over the message box (the mic button
   shows its own state, and the chat shows when a reply is coming) */
.input-box .eta-bar,
.input-box .progress-bar,
.input-box .progress-level,
.input-box .progress-text,
.input-box .meta-text,
.input-box .loader{
    display:none !important;
}

#mic-btn{
    --mic-icon:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='9' y='2' width='6' height='12' rx='3'/%3E%3Cpath d='M5 10v1a7 7 0 0 0 14 0v-1'/%3E%3Cpath d='M12 18v4'/%3E%3C/svg%3E");
    position:absolute !important;
    right:8px;
    top:50%;
    transform:translateY(-50%);
    z-index:5;
    width:34px !important;
    min-width:34px !important;
    max-width:34px !important;
    height:34px !important;
    padding:0 !important;
    border:none !important;
    border-radius:50% !important;
    background:transparent !important;
    box-shadow:none !important;
    color:var(--text-dim) !important;
    font-size:0 !important;
}

#mic-btn::before{
    content:"";
    display:block;
    width:18px;
    height:18px;
    margin:auto;
    background-color:currentColor;
    -webkit-mask:var(--mic-icon) center / contain no-repeat;
    mask:var(--mic-icon) center / contain no-repeat;
}

#mic-btn:hover{
    background:var(--surface-alt) !important;
    color:var(--text-main) !important;
}

#mic-btn.recording{
    background:#fee2e2 !important;
    color:#dc2626 !important;
    animation:mic-pulse 1.2s ease-in-out infinite;
}

#mic-btn.busy{
    pointer-events:none;
}

#mic-btn.busy::before{
    opacity:.45;
}

/* Status label to the left of the mic: "Listening…" / "Transcribing…" */
#mic-btn::after{
    content:none;
    position:absolute;
    right:calc(100% + 6px);
    top:50%;
    transform:translateY(-50%);
    font-size:13px;
    font-weight:500;
    white-space:nowrap;
    pointer-events:none;
}

#mic-btn.recording::after{
    content:"● Listening…";
    color:#dc2626;
}

#mic-btn.busy::after{
    content:"Transcribing…";
    color:var(--text-dim);
}

/* Keep typed text clear of the label */
.input-box:has(#mic-btn.recording) textarea,
.input-box:has(#mic-btn.busy) textarea{
    padding-right:150px !important;
}

@keyframes mic-pulse{
    0%,100%{ box-shadow:0 0 0 0 rgba(220,38,38,.35); }
    50%{ box-shadow:0 0 0 6px rgba(220,38,38,0); }
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


# Browser-side recording for the mic button. Returns [text, audio]:
# audio is "" when recording starts, a base64 data URL when it stops,
# or "ERROR:<reason>" if the microphone can't be used.
MIC_JS = """
async (text, _audio) => {
    const btn = document.querySelector('#mic-btn');

    if (!window.__micRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            const chunks = [];
            recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
            recorder.start();
            window.__micRecording = { recorder, chunks, stream };
            btn.classList.add('recording');
            btn.title = 'Stop recording';
            return [text, ''];
        } catch (err) {
            return [text, 'ERROR:' + (err.message || err.name)];
        }
    }

    const { recorder, chunks, stream } = window.__micRecording;
    window.__micRecording = null;
    await new Promise((resolve) => { recorder.onstop = resolve; recorder.stop(); });
    stream.getTracks().forEach((track) => track.stop());
    btn.classList.remove('recording');
    btn.classList.add('busy');
    btn.title = 'Voice input';

    const blob = new Blob(chunks, { type: recorder.mimeType });
    const dataUrl = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.readAsDataURL(blob);
    });
    return [text, dataUrl];
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

                # Preview of an image chosen with 📎 (until it is sent)
                with gr.Row(visible=False, elem_classes="attach-preview") as attach_preview:
                    preview_image = gr.Image(
                        show_label=False,
                        interactive=False,
                        container=False,
                        buttons=[],
                        height=64,
                        width=64,
                        elem_id="attach-thumb",
                    )
                    remove_image = gr.Button("✕", elem_id="attach-remove")

                with gr.Row(elem_classes="input-row"):
                    with gr.Column(scale=8, elem_classes="input-box"):
                        textbox = gr.Textbox(
                            placeholder="Message your assistant...",
                            show_label=False,
                            container=False,
                        )
                        attach = gr.UploadButton(
                            "Attach image",
                            file_types=["image"],
                            type="filepath",
                            elem_id="attach-btn",
                        )
                        mic = gr.Button("Voice input", elem_id="mic-btn")
                    send = gr.Button("Send", elem_id="send-btn", scale=1)

                # Carries the recording from the browser to dictate()
                mic_audio = gr.Textbox(visible=False)
                # Path of the image waiting to be sent with the next message
                pending_image = gr.State(None)

    # ==================================================================== #
    #  Events
    # ==================================================================== #

    chat_inputs = [textbox, chatbot, pending_image]
    chat_outputs = [textbox, chatbot, welcome_panel, pending_image, attach_preview]

    send.click(fn=respond, inputs=chat_inputs, outputs=chat_outputs)
    textbox.submit(fn=respond, inputs=chat_inputs, outputs=chat_outputs)

    attach.upload(
        fn=attach_image,
        inputs=attach,
        outputs=[pending_image, attach_preview, preview_image],
        show_progress="hidden",
    )

    remove_image.click(
        fn=remove_attachment,
        outputs=[pending_image, attach_preview, preview_image],
        show_progress="hidden",
    )

    # First click starts recording in the browser; second click stops it
    # and sends the audio to dictate(), which fills in the message box.
    mic.click(
        fn=dictate,
        inputs=[textbox, mic_audio],
        outputs=[textbox, mic_audio],
        js=MIC_JS,
        # The mic button shows its own state; no loading bar on the box
        show_progress="hidden",
    ).then(
        fn=None,
        js="() => document.querySelector('#mic-btn')?.classList.remove('busy')",
        show_progress="hidden",
    )

    new_chat.click(
        fn=clear_chat,
        outputs=[chatbot, welcome_panel, pending_image, attach_preview],
    )

    for ex_btn in (ex1, ex2, ex3, ex4):
        ex_btn.click(fn=use_example, inputs=ex_btn, outputs=textbox)

    calendar.click(fn=open_calendar, inputs=[], outputs=[])
    gmail.click(fn=open_gmail, inputs=[], outputs=[])


if __name__ == "__main__":
    demo.launch(theme=theme, css=custom_css)
