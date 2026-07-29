from __future__ import annotations

import json
import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import Any

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict
from chat import run_model_tool_loop, trim_history, now_iso, safe_slug, write_transcript
from run_eval import evaluate_phase_b

# -------------------------------------------------------------
# 1. Page Configuration & Custom CSS
# -------------------------------------------------------------
st.set_page_config(
    page_title="Research Agent Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Aesthetics (Glassmorphism & Neon details)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, .title-text {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
    }
    .main-title {
        background: linear-gradient(90deg, #FF4B4B, #FF8383, #8514FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.1rem;
    }
    .subtitle-text {
        color: #8C8C8C;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .hash-badge {
        font-family: monospace;
        background-color: #262730;
        color: #FF4B4B;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .mismatch-card {
        background: rgba(255, 75, 75, 0.1);
        border: 1px solid rgba(255, 75, 75, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
    }
    .success-card {
        background: rgba(75, 255, 75, 0.15);
        border: 1px solid rgba(75, 255, 75, 0.4);
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

# -------------------------------------------------------------
# 2. Session State Initialization
# -------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "transcript_id" not in st.session_state:
    st.session_state.transcript_id = f"st_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "last_results" not in st.session_state:
    st.session_state.last_results = None

# Load base eval cases
@st.cache_data
def load_eval_cases():
    eval_file = ROOT / "data" / "eval_base.json"
    if eval_file.exists():
        try:
            return json.loads(eval_file.read_text(encoding="utf-8"))["cases"]
        except Exception:
            return []
    return []

eval_cases = load_eval_cases()

def get_case_status_for_version(version_label: str) -> dict[str, bool]:
    runs_dir = ROOT / "runs"
    if not runs_dir.exists():
        return {}
    # Find all json files matching {version_label}_*
    run_files = list(runs_dir.glob(f"{version_label}_*.json"))
    if not run_files:
        return {}
    # Sort by modification time to get the latest run of that version
    run_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_run_file = run_files[0]
    try:
        data = json.loads(latest_run_file.read_text(encoding="utf-8"))
        # Map case_id -> passed (True/False)
        return {result["id"]: result["result"]["passed"] for result in data.get("results", [])}
    except Exception:
        return {}

# -------------------------------------------------------------
# 3. Sidebar - Cấu hình & Phiên bản
# -------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="title-text" style="font-size: 1.5rem; margin-bottom: 1rem;">⚙️ Settings</div>', unsafe_allow_html=True)
    
    # Model Provider Settings
    provider_choice = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    provider = make_provider(provider_choice)
    default_model = getattr(provider, "default_model", "gpt-4o-mini")
    model_name = st.text_input("Model", value=default_model)
    
    st.markdown("---")
    
    # Version Selector
    st.markdown('<div class="title-text" style="font-size: 1.2rem; margin-bottom: 0.5rem;">🔖 Select Prompt/Tool Version</div>', unsafe_allow_html=True)
    version = st.selectbox("Version", ["v0", "v1", "v2", "v3", "v4"], index=4)
    
    # Reset chat on version change
    if "current_version" not in st.session_state:
        st.session_state.current_version = version
    elif st.session_state.current_version != version:
        st.session_state.current_version = version
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.last_results = None
        st.session_state.transcript_id = f"st_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
        
    # Load corresponding files from history
    history_dir = ARTIFACTS_DIR / "history"
    prompt_file = history_dir / f"system_prompt_{version}.md"
    tools_file = history_dir / f"tools_{version}.yaml"
    
    # Fallback to current files if history is missing
    if not prompt_file.exists():
        prompt_file = ARTIFACTS_DIR / "system_prompt.md"
    if not tools_file.exists():
        tools_file = ARTIFACTS_DIR / "tools.yaml"
        
    system_prompt = prompt_file.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_file)
    openai_tools = to_openai_tools(tool_declarations)
    artifact_version = build_artifact_version(version, prompt_file, tools_file)
    
    with st.expander("👁️ View System Prompt & Tools"):
        tabs = st.tabs(["System Prompt", "Tools Decl"])
        with tabs[0]:
            st.code(system_prompt, language="markdown")
        with tabs[1]:
            st.code(tools_file.read_text(encoding="utf-8"), language="yaml")
            
    st.markdown("---")
    
    # Test Case Loader
    st.markdown('<div class="title-text" style="font-size: 1.2rem; margin-bottom: 0.5rem;">🎯 Base Eval Runner</div>', unsafe_allow_html=True)
    if eval_cases:
        # Load run status for the selected version
        case_status = get_case_status_for_version(version)
        
        # Build custom labels and priorities (0: Failed, 1: Untested, 2: Passed)
        case_items = []
        for c in eval_cases:
            c_id = c["id"]
            status = case_status.get(c_id, None)
            if status is False:
                label = f"❌ [FAIL] {c_id}"
                priority = 0
            elif status is True:
                label = f"✅ [PASS] {c_id}"
                priority = 2
            else:
                label = f"⚪ [UNTESTED] {c_id}"
                priority = 1
            query_preview = c.get('query', c.get('turns', [{}])[-1].get('content', ''))[:25]
            full_label = f"{label} ({query_preview}...)"
            case_items.append((c, full_label, priority))
            
        # Sort so Failed (0) comes first, then Untested (1), then Passed (2)
        case_items.sort(key=lambda x: (x[2], x[0]["id"]))
        
        # Build the final options list for Streamlit selectbox
        options = [("None", "Select a case...")] + [(item[0], item[1]) for item in case_items]
        selected_option = st.selectbox(
            "Load Test Case",
            options,
            format_func=lambda x: x[1],
            index=0
        )
        
        if selected_option[0] != "None":
            case = selected_option[0]
            st.session_state.selected_case = case
            
            # Show case details
            difficulty = case["metadata"].get("difficulty", "medium")
            skill = case["metadata"].get("skill", "n/a")
            what_it_tests = case["metadata"].get("what_it_tests", "")
            
            st.markdown(f"""
            <div class="metric-card" style="font-size: 0.9rem;">
                <strong>Skill:</strong> {skill}<br>
                <strong>Difficulty:</strong> {difficulty}<br>
                <strong>Tests:</strong> <em>{what_it_tests}</em>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Load Test Case to Chat"):
                # Clear existing messages
                st.session_state.messages = []
                st.session_state.history = []
                st.session_state.last_results = None
                
                # Multi-turn load
                if "turns" in case:
                    # Load all but last turn as chat history
                    for turn in case["turns"][:-1]:
                        st.session_state.messages.append({"role": turn["role"], "content": turn["content"]})
                        st.session_state.history.append({"role": turn["role"], "content": turn["content"]})
                    # Use last turn as active input
                    st.session_state.active_input = case["turns"][-1]["content"]
                else:
                    # Single turn load
                    st.session_state.active_input = case.get("query") or case.get("input", "")
                st.rerun()
        else:
            st.session_state.selected_case = None
            
    st.markdown("---")
            
    # Version Log Summary (moved here)
    st.markdown('<div class="title-text" style="font-size: 1.2rem; margin-bottom: 0.5rem;">📈 Version Log Summary</div>', unsafe_allow_html=True)
    def get_version_log_summary() -> str:
        log_file = ROOT / "artifacts" / "version_log.csv"
        if not log_file.exists():
            return "No version log file found."
        try:
            import csv
            with open(log_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            if not rows:
                return "Version log is empty."
            md = "| Ver | Author | Metric | Before | After |\n|---|---|---|---|---|\n"
            for row in rows:
                md += f"| **{row.get('version')}** | {row.get('author')} | {row.get('metric_name')} | {row.get('metric_before')} | {row.get('metric_after')} |\n"
            return md
        except Exception as e:
            return f"Error loading log: {e}"
            
    st.markdown(get_version_log_summary())

    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.last_results = None
        st.session_state.transcript_id = f"st_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
        st.rerun()

# -------------------------------------------------------------
# 4. Main Panel UI
# -------------------------------------------------------------
st.markdown('<div class="main-title">🤖 Research Agent Workspace</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle-text">Interactive playground with trace logging & verification evaluation. Running on <b>{model_name}</b> (Version <b>{version}</b>).</div>', unsafe_allow_html=True)

# Create transcripts path
transcripts_dir = ROOT / "transcripts"
transcript_path = transcripts_dir / f"{st.session_state.transcript_id}.transcript.json"

transcript: dict[str, Any] = {
    "transcript_id": st.session_state.transcript_id,
    **artifact_version_dict(artifact_version),
    "provider": provider_choice,
    "model": model_name,
    "system_prompt": str(prompt_file),
    "tools": str(tools_file),
    "history_window": 5,
    "max_tool_rounds": 4,
    "created_at": now_iso(),
    "updated_at": now_iso(),
    "turns": [],
}

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
# Handle user query input
if "active_input" in st.session_state:
    user_query = st.session_state.active_input
    del st.session_state.active_input
    # Automatically submit
    submit_query = True
else:
    user_query = st.chat_input("Hỏi tôi về tin tức AI, tweets, bài báo arXiv hoặc nhờ gửi Telegram...")
    submit_query = False

if user_query or submit_query:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)
        
    # Run Agent Loop
    with st.chat_message("assistant"):
        st.markdown("**🧠 Agent is thinking...**")
        
        # Prepare messages in eval/chat contract format
        # If the case loaded is a multi-turn eval case, run_eval.py uses a formatted system/context prompt
        # But to allow natural testing on the UI, we send system prompt and message history:
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(st.session_state.history, 5),
            {"role": "user", "content": user_query},
        ]
        
        # We also support formatted context if it is a multi-turn case being loaded directly to test evaluator
        case = st.session_state.selected_case
        if case and "turns" in case:
            # We want to match run_eval's prompt structure for multi-turn cases to ensure correctness evaluation:
            turns = case["turns"]
            previous = turns[:-1]
            latest = turns[-1]["content"]
            # If the user input matches the latest turn, format it exactly like run_eval does!
            if user_query == latest:
                previous_text = "\n".join(
                    f"- Earlier {item['role']} turn {index + 1}: {item['content']}"
                    for index, item in enumerate(previous)
                )
                content = (
                    "Conversation context for a multi-turn eval.\n"
                    "Use earlier turns only as context. Do not answer earlier turns and do not call tools for them.\n\n"
                    f"{previous_text}\n\n"
                    f"Latest user turn to answer now: {latest}"
                )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
        
        # Containers for real-time trace
        trace_container = st.container()
        
        try:
            # Run model tool loop
            with st.spinner("Executing tool workflow..."):
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_name,
                    max_tool_rounds=4
                )
                
            assistant_text = result["assistant_text"]
            st.write(assistant_text)
            
            # Show tool traces
            with trace_container:
                if result["tool_events"]:
                    st.markdown("### 🔧 Tool Execution Trace")
                    for i, round_item in enumerate(result["rounds"]):
                        with st.expander(f"🔄 Round {round_item['round']}", expanded=True):
                            if round_item["tool_calls"]:
                                for call in round_item["tool_calls"]:
                                    st.markdown(f"**Call Tool:** `{call['name']}`")
                                    st.json(call["args"])
                            if round_item["tool_results"]:
                                for res in round_item["tool_results"]:
                                    st.markdown(f"**Result for** `{res['tool']}`:")
                                    st.json(res["result"])
                            if round_item.get("assistant_text"):
                                st.markdown(f"**Assistant:** {round_item['assistant_text']}")
                else:
                    st.info("ℹ️ No tools were called. Answered directly.")
            
            # Save history & state
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            st.session_state.history.append({"role": "user", "content": user_query})
            st.session_state.history.append({"role": "assistant", "content": assistant_text})
            
            # -------------------------------------------------------------
            # 5. Verification Evaluation (Đánh giá Đúng/Sai)
            # -------------------------------------------------------------
            if case:
                # Compile actual tool calls
                calls = [{"name": call["tool"], "args": call["args"]} for call in result["tool_events"]]
                eval_res = evaluate_phase_b(case, calls, assistant_text)
                st.session_state.last_results = eval_res
                
            # Log Transcript
            turn_record = {
                "turn_index": len(st.session_state.history) // 2,
                "started_at": now_iso(),
                "user": user_query,
                "status": result["status"],
                "assistant_text": assistant_text,
                "rounds": result["rounds"],
                "tool_events": result["tool_events"],
                "ended_at": now_iso(),
            }
            transcript["turns"].append(turn_record)
            write_transcript(transcript_path, transcript)
            
        except Exception as exc:
            st.error(f"❌ Error during execution: {exc}")
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {exc}"})

# Show evaluation results if available
if st.session_state.last_results:
    res = st.session_state.last_results
    st.markdown("---")
    st.markdown("### 📊 Automated Grader Evaluation")
    
    if res["passed"]:
        st.markdown(f"""
        <div class="success-card">
            <h4 style="color: #4BFF4B; margin: 0 0 8px 0;">✅ CORRECT (ĐÚNG)</h4>
            The agent routed to the correct tool(s) with correct argument constraints matching the test case expectation.
        </div>
        """, unsafe_allow_html=True)
    else:
        failures_html = "".join([f"<li>{fail}</li>" for fail in res["failures"]])
        st.markdown(f"""
        <div class="mismatch-card">
            <h4 style="color: #FF4B4B; margin: 0 0 8px 0;">❌ INCORRECT (SAI)</h4>
            <strong>Mismatch Category:</strong> {res['observed_mismatch']}<br>
            <strong>Failures:</strong>
            <ul style="margin-top: 5px; margin-bottom: 0;">
                {failures_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("**Expected Action:**")
    st.json(st.session_state.selected_case["expect"])
