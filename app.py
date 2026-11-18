"""
AI-Based Academic Content Generator
University Prompt Engineering Course Project
Tech Stack: Python, Streamlit, Prompt Engineering (RTCACO Framework)

Core Capabilities:
  • Design prompts for notes, explanations, and examples
  • Compare outputs for different prompt styles
  • Optimize prompts for clarity and depth
  • Document best prompt templates
"""

import streamlit as st
import datetime
from prompts import (
    build_study_notes_prompt,
    build_topic_explainer_prompt,
    build_worked_example_prompt,
    build_summary_prompt,
    build_mcq_prompt,
    build_exam_questions_prompt,
    get_prompt_styles_comparison,
    get_optimization_evolution,
    get_best_prompt_templates,
    get_prompt_engineering_comparison
)
from generator import generate_content, MULTI_LLM_REGISTRY, run_multi_llm_comparison

# ==============================================================================
# Page Configuration
# ==============================================================================
st.set_page_config(
    page_title="AI Academic Content Generator | University Lab",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# Custom University Theme CSS (Navy Blue, White, Light Blue)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .uni-header {
        background: linear-gradient(135deg, #0B2545 0%, #134074 100%);
        color: #FFFFFF;
        padding: 1.8rem 2.2rem;
        border-radius: 12px;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 20px rgba(11, 37, 69, 0.15);
        border-left: 6px solid #8DA9C4;
    }
    .uni-header h1 {
        color: #FFFFFF;
        margin: 0;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .uni-header p {
        color: #DCEBF7;
        margin: 0.4rem 0 0 0;
        font-size: 1.05rem;
        font-weight: 400;
    }
    .uni-badge {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.35);
        color: #FFFFFF;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 0.6rem;
    }

    .academic-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border-top: 3px solid #134074;
    }
    
    .status-badge-demo {
        background-color: #EEF4F8;
        color: #0B2545;
        border: 1px solid #8DA9C4;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1rem;
    }
    
    .status-badge-live {
        background-color: #E6F4EA;
        color: #137333;
        border: 1px solid #CEEAD6;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1rem;
    }

    .comparison-card {
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .naive-box {
        background-color: #FFF5F5;
        border: 1px solid #FEB2B2;
        border-left: 5px solid #E53E3E;
    }
    .structured-box {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 5px solid #16A34A;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# Header Banner
# ==============================================================================
st.markdown("""
<div class="uni-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <h1>🎓 AI-Based Academic Content Generator</h1>
            <p>University Laboratory for Prompt Engineering & Pedagogical Content Synthesis</p>
        </div>
        <div>
            <span class="uni-badge">RTCACO Prompt Architecture</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# Sidebar: Configuration & Controls
# ==============================================================================
st.sidebar.markdown("### ⚙️ Academic Control Panel")

# Quick Sample Presets
preset_choice = st.sidebar.selectbox(
    "💡 Quick Fill Sample Presets:",
    [
        "Custom Input",
        "Computer Science: Backpropagation & Gradient Descent",
        "Biology: CRISPR-Cas9 Gene Editing Mechanism",
        "Economics: Game Theory & Nash Equilibrium",
        "Physics: Quantum Superposition & Wave Mechanics",
        "Medicine: Type 2 Diabetes Pathophysiology"
    ]
)

presets = {
    "Computer Science: Backpropagation & Gradient Descent": {
        "subject": "Computer Science",
        "topic": "Backpropagation & Gradient Descent in Deep Neural Networks",
        "level": "Undergraduate",
        "difficulty": "Intermediate",
        "focus": "Chain rule derivation and vanishing gradients"
    },
    "Biology: CRISPR-Cas9 Gene Editing Mechanism": {
        "subject": "Molecular Biology",
        "topic": "CRISPR-Cas9 Mechanism & Targeted Gene Editing",
        "level": "Postgraduate",
        "difficulty": "Advanced",
        "focus": "Guide RNA design and off-target cleavages"
    },
    "Economics: Game Theory & Nash Equilibrium": {
        "subject": "Economics",
        "topic": "Nash Equilibrium & Strategic Interactions",
        "level": "Undergraduate",
        "difficulty": "Intermediate",
        "focus": "Prisoner's dilemma and dominant strategies"
    },
    "Physics: Quantum Superposition & Wave Mechanics": {
        "subject": "Quantum Physics",
        "topic": "Quantum Superposition & Schrödinger Wave Equation",
        "level": "Postgraduate",
        "difficulty": "Advanced",
        "focus": "Wave-function collapse and Hilbert space representation"
    },
    "Medicine: Type 2 Diabetes Pathophysiology": {
        "subject": "Medicine & Endocrinology",
        "topic": "Type 2 Diabetes Mellitus Pathophysiology",
        "level": "Undergraduate",
        "difficulty": "Intermediate",
        "focus": "Insulin resistance vs beta-cell dysfunction"
    }
}

active_preset = presets.get(preset_choice, None)

default_subject = active_preset["subject"] if active_preset else "Computer Science"
default_topic = active_preset["topic"] if active_preset else "Backpropagation & Gradient Descent"
default_level_idx = ["High School", "Undergraduate", "Postgraduate", "Doctoral / Professional"].index(active_preset["level"]) if active_preset else 1
default_diff_idx = ["Foundational", "Intermediate", "Advanced"].index(active_preset["difficulty"]) if active_preset else 1
default_focus = active_preset["focus"] if active_preset else ""

# Input Form
subject = st.sidebar.text_input("📚 Subject / Discipline *", value=default_subject, placeholder="e.g., Computer Science, Biochemistry, Economics")
topic = st.sidebar.text_input("🎯 Topic / Subtopic *", value=default_topic, placeholder="e.g., Backpropagation, Photosynthesis, Fiscal Policy")

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    academic_level = st.selectbox(
        "🎓 Academic Level",
        ["High School", "Undergraduate", "Postgraduate", "Doctoral / Professional"],
        index=default_level_idx
    )
with col_sb2:
    difficulty = st.selectbox(
        "⚡ Difficulty Tier",
        ["Foundational", "Intermediate", "Advanced"],
        index=default_diff_idx
    )

content_length = st.sidebar.select_slider(
    "📏 Desired Scope / Length",
    options=["Concise", "Standard", "Comprehensive"],
    value="Standard"
)

focus_areas = st.sidebar.text_input(
    "🔍 Specific Sub-focus / Keywords (Optional)",
    value=default_focus,
    placeholder="e.g., Practical case studies, mathematical derivations"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔌 Generation Engine")

api_provider = st.sidebar.radio(
    "Engine Mode:",
    ["Demo Mode (No API Key Required)", "Ollama (Local; No API Key)", "Google Gemini", "OpenAI"],
    index=0,
    help="Use Demo Mode offline, Ollama with a locally installed model, or a hosted API provider."
)

api_key = ""
api_model = "llama3.2:3b"
if api_provider == "Ollama (Local; No API Key)":
    api_model = st.sidebar.text_input(
        "Ollama model:",
        value=api_model,
        help="The model must already be downloaded in Ollama, for example llama3.2:3b."
    ).strip()
    st.sidebar.caption("Runs on this computer; no API key is used.")
elif api_provider != "Demo Mode (No API Key Required)":
    api_key = st.sidebar.text_input(
        f"Enter {api_provider} API Key:",
        type="password",
        placeholder="Paste API Key here...",
        help="Your key is never logged or stored. It is used only for real-time requests."
    )
    st.sidebar.caption("🔒 Key is kept in memory for this session only.")
else:
    st.sidebar.info("💡 **Demo Mode Active:** Operates offline with pre-compiled university templates. No API key needed!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔀 Multi-LLM Comparison Keys")
st.sidebar.caption("Enter keys below to test the **same prompt across multiple LLMs** in the Prompt Lab.")

multi_gemini_key = st.sidebar.text_input(
    "Google Gemini API Key:",
    type="password",
    key="multi_gemini_key",
    placeholder="For multi-LLM comparison..."
)
multi_openai_key = st.sidebar.text_input(
    "OpenAI API Key:",
    type="password",
    key="multi_openai_key",
    placeholder="For multi-LLM comparison..."
)

st.sidebar.markdown("---")
st.sidebar.caption("Project: AI-Based Academic Content Generator\nCourse: Prompt Engineering 2026")

# ==============================================================================
# Navigation Tabs
# ==============================================================================
tabs = st.tabs([
    "📚 Study Notes",
    "💡 Topic Explainer",
    "🧪 Worked Examples",
    "📝 Revision Summary",
    "🎯 MCQ Assessment",
    "✍️ Exam Questions",
    "🔬 Prompt Engineering Lab",
    "ℹ️ About Project"
])

# Helper for Content Generation
def handle_generation(content_type_name: str, tab_container):
    with tab_container:
        st.subheader(f"{content_type_name} Generator")
        
        # Validation checks
        if not subject.strip() or not topic.strip():
            st.warning("⚠️ **Input Required:** Please enter both a **Subject** and a **Topic** in the sidebar before generating content.")
            return

        col_act1, col_act2 = st.columns([1, 4])
        with col_act1:
            gen_button = st.button(f"Generate {content_type_name}", key=f"btn_{content_type_name}", use_container_width=True)
            
        session_key = f"output_v2_{content_type_name}_{api_provider}_{api_model}_{subject}_{topic}_{academic_level}_{difficulty}_{content_length}"

        if gen_button:
            with st.spinner(f"Synthesizing {content_type_name} using RTCACO framework..."):
                if api_provider == "Google Gemini":
                    engine_name = "Google Gemini"
                elif api_provider == "OpenAI":
                    engine_name = "OpenAI"
                elif api_provider.startswith("Ollama"):
                    engine_name = "Ollama"
                else:
                    engine_name = "Demo Mode"
                content, mode_label, prompt_dict = generate_content(
                    content_type=content_type_name,
                    subject=subject,
                    topic=topic,
                    level=academic_level,
                    difficulty=difficulty,
                    length=content_length,
                    focus=focus_areas,
                    api_provider=engine_name,
                    api_key=api_key,
                    api_model=api_model
                )
                st.session_state[session_key] = {
                    "content": content,
                    "mode_label": mode_label,
                    "prompt_dict": prompt_dict,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

        # Display result if available in session state
        if session_key in st.session_state:
            result = st.session_state[session_key]
            
            # Status Badge
            if "Ollama Error Fallback" in result["mode_label"]:
                st.info("Ollama did not generate this content; a demo template is shown. See the app log for details.")
            elif "Demo Mode" in result["mode_label"]:
                st.markdown(f'<div class="status-badge-demo">ℹ️ {result["mode_label"]} | Generated at {result["timestamp"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-badge-live">{result["mode_label"]} | Generated at {result["timestamp"]}</div>', unsafe_allow_html=True)

            # Action / Download row
            d_col1, d_col2, d_col3 = st.columns([2, 2, 4])
            filename_base = f"{topic.replace(' ', '_')}_{content_type_name.replace(' ', '_')}"
            with d_col1:
                st.download_button(
                    label="📥 Download Markdown (.md)",
                    data=result["content"],
                    file_name=f"{filename_base}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with d_col2:
                st.download_button(
                    label="📄 Download Text (.txt)",
                    data=result["content"],
                    file_name=f"{filename_base}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            st.markdown("---")
            
            # Content Rendering
            st.markdown(result["content"])

            st.markdown("---")
            # Prompt Inspector Accordion
            with st.expander("🔍 Inspect Structured Prompt Used (RTCACO Specification)", expanded=False):
                st.caption("This displays the exact multi-part prompt template engineered for this academic task:")
                p = result["prompt_dict"]
                st.markdown(f"**[ROLE / PERSONA]:**\n`{p['role']}`")
                st.markdown(f"**[TASK]:**\n`{p['task']}`")
                st.markdown(f"**[CONTEXT]:**\n`{p['context']}`")
                st.markdown(f"**[AUDIENCE]:**\n`{p['audience']}`")
                st.markdown(f"**[CONSTRAINTS & GUARDRAILS]:**\n`{p['constraints']}`")
                st.markdown(f"**[OUTPUT SPECIFICATION]:**\n```markdown\n{p['output_format']}\n```")


# ==============================================================================
# TAB 1: Study Notes
# ==============================================================================
handle_generation("Study Notes", tabs[0])

# ==============================================================================
# TAB 2: Topic Explainer
# ==============================================================================
handle_generation("Topic Explainer", tabs[1])

# ==============================================================================
# TAB 3: Worked Examples
# ==============================================================================
handle_generation("Worked Examples", tabs[2])

# ==============================================================================
# TAB 4: Summary Generator
# ==============================================================================
handle_generation("Summary", tabs[3])

# ==============================================================================
# TAB 5: MCQ Generator
# ==============================================================================
handle_generation("Multiple-Choice Questions", tabs[4])

# ==============================================================================
# TAB 6: Exam Questions
# ==============================================================================
handle_generation("Exam Questions", tabs[5])

# ==============================================================================
# TAB 7: Prompt Engineering Lab (Design, Compare, Optimize, Document)
# ==============================================================================
with tabs[6]:
    st.subheader("🔬 Prompt Engineering Laboratory & Research Workbench")
    st.markdown("""
    This laboratory addresses the four foundational pillars of academic prompt engineering:
    1. **Design prompts for notes, explanations, and examples**
    2. **Compare outputs for different prompt styles**
    3. **Optimize prompts for clarity and depth**
    4. **Document best prompt templates**
    """)
    
    lab_sub_tabs = st.tabs([
        "1. 📐 Design Prompts (Notes/Explanations/Examples)",
        "2. ⚖️ Compare Outputs for 4 Prompt Styles",
        "3. 📈 Optimize Prompts for Clarity & Depth",
        "4. 📑 Document Best Prompt Templates",
        "5. 🤖 Multi-LLM Comparison (Test Across Models)"
    ])

    # --------------------------------------------------------------------------
    # SUB-TAB 1: Design prompts for notes, explanations, and examples
    # --------------------------------------------------------------------------
    with lab_sub_tabs[0]:
        st.markdown("### 📐 Formal Prompt Design: Notes, Explanations, and Examples")
        st.write(
            "Each academic learning modality requires distinct cognitive scaffolding. "
            "Below are the specific architectural prompt designs engineered for the current topic: "
            f"**{topic}** ({subject})."
        )
        
        design_choice = st.radio(
            "Select Modality to Inspect Prompt Design:",
            ["Academic Study Notes", "Conceptual Explanations", "Quantitative Worked Examples"],
            horizontal=True
        )
        
        if design_choice == "Academic Study Notes":
            p_obj = build_study_notes_prompt(subject, topic, academic_level, difficulty, content_length, focus_areas)
            st.info("🎯 **Design Scaffolding:** Emphasizes formal definitions, learning outcomes, theoretical foundations, and active-recall checkpoints.")
        elif design_choice == "Conceptual Explanations":
            p_obj = build_topic_explainer_prompt(subject, topic, academic_level, difficulty, content_length, focus_areas)
            st.info("🎯 **Design Scaffolding:** Eliminates extraneous cognitive load by anchoring abstract theory in high-fidelity everyday analogies.")
        else:
            p_obj = build_worked_example_prompt(subject, topic, academic_level, difficulty, content_length, focus_areas)
            st.info("🎯 **Design Scaffolding:** Enforces explicit initial boundary conditions, sanity checks, and warnings against common student mistakes.")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**[ROLE & PERSONA]:**\n`{p_obj['role']}`")
            st.markdown(f"**[TASK GOAL]:**\n`{p_obj['task']}`")
            st.markdown(f"**[CONTEXT & AUDIENCE]:**\n`{p_obj['context']}`\n\n*Target Audience:* `{p_obj['audience']}`")
        with c2:
            st.markdown(f"**[CONSTRAINTS & GUARDRAILS]:**\n```text\n{p_obj['constraints']}\n```")
            st.markdown(f"**[OUTPUT SPECIFICATION SCHEMA]:**\n```markdown\n{p_obj['output_format']}\n```")

    # --------------------------------------------------------------------------
    # SUB-TAB 2: Compare outputs for different prompt styles
    # --------------------------------------------------------------------------
    with lab_sub_tabs[1]:
        st.markdown("### ⚖️ Compare Outputs Across 4 Distinct Prompt Styles")
        st.write(
            "To understand the direct empirical impact of prompt design, we test four distinct prompt styles "
            f"on **{topic}** at the **{academic_level}** level:"
        )
        
        styles_data = get_prompt_styles_comparison(subject, topic, academic_level, content_type="Notes")
        
        style_cols = st.columns(4)
        for idx, s in enumerate(styles_data["styles"]):
            with style_cols[idx]:
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-top: 4px solid {s['badge_color']}; border-radius: 8px; padding: 12px; height: 100%;">
                    <h5 style="margin: 0; color: #0B2545;">{s['name']}</h5>
                    <span style="display:inline-block; font-size: 0.75rem; background: #EEF4F8; color: #134074; padding: 2px 8px; border-radius: 4px; margin: 4px 0;">{s['tag']}</span>
                    <hr style="margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;" />
                    <p style="font-size: 0.82rem; margin: 2px 0;"><strong>Clarity:</strong> {s['clarity_score']}/10</p>
                    <p style="font-size: 0.82rem; margin: 2px 0;"><strong>Depth:</strong> {s['depth_score']}/10</p>
                    <p style="font-size: 0.82rem; margin: 2px 0;"><strong>Schema Adherence:</strong> {s['compliance_score']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🔍 Side-by-Side Prompt & Output Inspector")
        
        active_style_idx = st.selectbox(
            "Select Style to inspect full Prompt & Generated Output:",
            options=[0, 1, 2, 3],
            format_func=lambda x: styles_data["styles"][x]["name"]
        )
        
        selected_style = styles_data["styles"][active_style_idx]
        
        out_col1, out_col2 = st.columns(2)
        with out_col1:
            st.markdown("##### 📝 Exact Prompt Sent to Model")
            st.code(selected_style["prompt"], language="markdown")
            st.warning(f"**Identified Weakness / Risk:** {selected_style['weakness']}")
            
        with out_col2:
            st.markdown("##### 📄 Resulting Pedagogical Output")
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px; max-height: 400px; overflow-y: auto;">
            """, unsafe_allow_html=True)
            st.markdown(selected_style["output"])
            st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # SUB-TAB 3: Optimize prompts for clarity and depth
    # --------------------------------------------------------------------------
    with lab_sub_tabs[2]:
        st.markdown("### 📈 Optimize Prompts for Clarity and Depth (Iterative Progression)")
        st.write(
            "Prompt engineering is an iterative optimization science. Below is the multi-stage optimization "
            f"pipeline transitioning from an unconstrained query to an optimized RTCACO template for **{topic}**."
        )

        evolution = get_optimization_evolution(subject, topic, academic_level)
        
        for stage in evolution["stages"]:
            with st.expander(f"📍 {stage['version']} — Focus: {stage['focus']}", expanded=True):
                ec1, ec2 = st.columns([3, 2])
                with ec1:
                    st.caption("Prompt Engineering Formulation:")
                    st.code(stage["prompt"], language="text")
                    st.caption("Engineering Interventions:")
                    st.info(stage["interventions"])
                with ec2:
                    st.caption("Quality & Diagnostic Metrics:")
                    m = stage["metrics"]
                    st.metric("Clarity Score", f"{m['clarity']} / 10")
                    st.metric("Depth & Rigor Score", f"{m['depth']} / 10")
                    st.write(f"**Hallucination Risk:** `{m['hallucination_risk']}`")
                    st.write(f"**Format Adherence:** `{m['format_adherence']}`")
                    st.caption(f"**Diagnostic Critique:** {m['critique']}")

        st.markdown("---")
        st.markdown("#### 📊 Empirical Summary of Prompt Optimization")
        st.table(evolution["summary_table"])

    # --------------------------------------------------------------------------
    # SUB-TAB 4: Document best prompt templates
    # --------------------------------------------------------------------------
    with lab_sub_tabs[3]:
        st.markdown("### 📑 Document Best Prompt Templates (Golden Prompt Library)")
        st.write(
            "This repository documents the highest-performing, battle-tested prompt templates. "
            "These standardized templates can be copied and directly deployed in any LMS, instructional pipeline, or LLM interface."
        )

        golden_templates = get_best_prompt_templates()
        for t in golden_templates:
            with st.container():
                st.markdown(f"#### {t['title']}")
                st.caption(f"**Primary Use Case:** {t['use_case']}")
                
                with st.expander("📋 Click to View / Copy Complete Golden Template", expanded=False):
                    st.code(t["template"], language="markdown")
                
                st.markdown("**Core Architectural Scaffolds:**")
                for feat in t["key_features"]:
                    st.markdown(f"- 🔹 {feat}")
                st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #E2E8F0;' />", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # SUB-TAB 5: Multi-LLM Comparison (Test Same Prompt Across Multiple Models)
    # --------------------------------------------------------------------------
    with lab_sub_tabs[4]:
        st.markdown("### 🤖 Multi-LLM Comparison: Test Same Prompt Across Multiple Models")
        st.write(
            "A key requirement of evaluating prompt engineering quality is verifying that structured prompts "
            "deliver consistently better results **across different Large Language Models**, not just one. "
            "This lab sends the **exact same RTCACO prompt** to multiple LLMs simultaneously and displays "
            "a side-by-side comparison of their outputs, response times, and quality."
        )

        if not subject.strip() or not topic.strip():
            st.warning("⚠️ Enter a **Subject** and **Topic** in the sidebar to run Multi-LLM comparison.")
        else:
            # Content type selector
            multi_content_type = st.selectbox(
                "Select Content Type to Compare:",
                ["Study Notes", "Topic Explainer", "Worked Examples", "Summary", "Multiple-Choice Questions", "Exam Questions"],
                key="multi_llm_content_type"
            )

            # Build the prompt for selected content type
            prompt_builders = {
                "Study Notes": build_study_notes_prompt,
                "Topic Explainer": build_topic_explainer_prompt,
                "Worked Examples": build_worked_example_prompt,
                "Summary": build_summary_prompt,
                "Multiple-Choice Questions": build_mcq_prompt,
                "Exam Questions": build_exam_questions_prompt
            }
            multi_prompt = prompt_builders[multi_content_type](
                subject, topic, academic_level, difficulty, content_length, focus_areas
            )

            # Show the prompt being sent
            with st.expander("📋 View the RTCACO Prompt Being Sent to All Models", expanded=False):
                st.code(multi_prompt["full_prompt"], language="markdown")

            st.markdown("---")
            st.markdown("#### Select LLM Models to Compare")

            # API key status display
            has_gemini = bool(multi_gemini_key.strip())
            has_openai = bool(multi_openai_key.strip())

            if not has_gemini and not has_openai:
                st.warning(
                    "⚠️ **No API keys provided.** Enter your Google Gemini and/or OpenAI API keys in the "
                    "**🔀 Multi-LLM Comparison Keys** section in the sidebar to enable live comparison."
                )
                st.info(
                    "💡 **For your Ma'am's demonstration:** Enter at least one Gemini key and one OpenAI key "
                    "to show cross-model comparison. Even a single provider with multiple models works!"
                )

            # Model selection checkboxes
            selected_models = []
            mcol1, mcol2 = st.columns(2)

            with mcol1:
                st.markdown(f"""
                <div style="background: {'#F0FDF4' if has_gemini else '#FFF5F5'}; border: 1px solid {'#BBF7D0' if has_gemini else '#FEB2B2'}; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <strong>🔵 Google Gemini</strong> {'✅ Key Provided' if has_gemini else '❌ No Key'}
                </div>
                """, unsafe_allow_html=True)
                if has_gemini:
                    for m in MULTI_LLM_REGISTRY["Google Gemini"]["models"]:
                        if st.checkbox(f"{m['display']} ({m['tier']})", key=f"mlm_{m['id']}", value=(m['id'] == 'gemini-2.0-flash')):
                            selected_models.append({"provider": "Google Gemini", "model_id": m["id"]})

            with mcol2:
                st.markdown(f"""
                <div style="background: {'#F0FDF4' if has_openai else '#FFF5F5'}; border: 1px solid {'#BBF7D0' if has_openai else '#FEB2B2'}; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <strong>🟢 OpenAI</strong> {'✅ Key Provided' if has_openai else '❌ No Key'}
                </div>
                """, unsafe_allow_html=True)
                if has_openai:
                    for m in MULTI_LLM_REGISTRY["OpenAI"]["models"]:
                        if st.checkbox(f"{m['display']} ({m['tier']})", key=f"mlm_{m['id']}", value=(m['id'] == 'gpt-4o-mini')):
                            selected_models.append({"provider": "OpenAI", "model_id": m["id"]})

            st.markdown("---")

            # Run comparison button
            run_btn = st.button(
                f"🚀 Run Comparison Across {len(selected_models)} Model(s)",
                disabled=(len(selected_models) < 1),
                use_container_width=True,
                key="btn_multi_llm_run"
            )

            session_key_multi = f"multi_llm_{subject}_{topic}_{multi_content_type}_{academic_level}"

            if run_btn and selected_models:
                api_keys_map = {
                    "Google Gemini": multi_gemini_key.strip(),
                    "OpenAI": multi_openai_key.strip()
                }
                with st.spinner(f"🔄 Sending RTCACO prompt to {len(selected_models)} LLM(s)... Please wait."):
                    results = run_multi_llm_comparison(multi_prompt, selected_models, api_keys_map)
                st.session_state[session_key_multi] = {
                    "results": results,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "content_type": multi_content_type,
                    "prompt_used": multi_prompt["full_prompt"]
                }

            # Display results
            if session_key_multi in st.session_state:
                stored = st.session_state[session_key_multi]
                results = stored["results"]
                st.success(f"✅ Multi-LLM comparison completed at {stored['timestamp']} for **{stored['content_type']}**")

                # Summary metrics table
                st.markdown("#### 📊 Cross-Model Performance Summary")
                summary_rows = []
                for r in results:
                    status_icon = "✅" if r["status"] == "success" else ("🔑" if r["status"] == "no_key" else "❌")
                    output_len = len(r["output"]) if r["output"] else 0
                    word_count = len(r["output"].split()) if r["output"] else 0
                    summary_rows.append({
                        "Status": status_icon,
                        "Provider": r["provider"],
                        "Model": r["display_name"],
                        "Response Time": f"{r['time_seconds']}s" if r["time_seconds"] > 0 else "N/A",
                        "Output Length": f"{output_len:,} chars",
                        "Word Count": f"{word_count:,} words",
                        "Error": r.get("error", "None") or "None"
                    })
                st.table(summary_rows)

                # Side-by-side output comparison
                st.markdown("#### 📄 Side-by-Side Output Comparison")
                successful = [r for r in results if r["status"] == "success"]

                if not successful:
                    st.error("No successful responses received. Please check your API keys and try again.")
                else:
                    output_cols = st.columns(min(len(successful), 3))
                    for idx, r in enumerate(successful):
                        col_idx = idx % min(len(successful), 3)
                        with output_cols[col_idx]:
                            st.markdown(f"""
                            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-top: 4px solid #134074; border-radius: 8px; padding: 10px;">
                                <strong>{r['display_name']}</strong><br/>
                                <span style="font-size: 0.8rem; color: #64748B;">{r['provider']} | {r['time_seconds']}s</span>
                            </div>
                            """, unsafe_allow_html=True)

                    # Tabbed output view for each model
                    if len(successful) > 0:
                        model_tabs = st.tabs([f"{r['display_name']} ({r['provider']})" for r in successful])
                        for idx, r in enumerate(successful):
                            with model_tabs[idx]:
                                st.markdown(f"**Model:** {r['display_name']} | **Provider:** {r['provider']} | **Response Time:** {r['time_seconds']}s")
                                st.download_button(
                                    f"📥 Download {r['display_name']} Output (.md)",
                                    data=r["output"],
                                    file_name=f"{topic.replace(' ', '_')}_{r['display_name'].replace(' ', '_')}.md",
                                    mime="text/markdown",
                                    key=f"dl_multi_{r['model_id']}"
                                )
                                st.markdown("---")
                                st.markdown(r["output"])

                    # Comparative analysis guidance
                    st.markdown("---")
                    st.markdown("#### 🔬 Cross-Model Evaluation Criteria")
                    st.markdown("""
                    When comparing outputs across multiple LLMs, evaluate using these dimensions:

                    | Evaluation Dimension | What to Check |
                    | :--- | :--- |
                    | **Structural Compliance** | Does the output follow the exact section schema (H1, H2, tables) specified in the RTCACO prompt? |
                    | **Terminology Precision** | Are technical terms formally defined with mathematical notation where applicable? |
                    | **Depth & Rigor** | Does the model provide worked examples, edge-case analysis, and misconception alerts? |
                    | **Hallucination Resistance** | Does the model invent fake citations, non-existent theorems, or unverifiable claims? |
                    | **Audience Calibration** | Is the cognitive complexity aligned with the specified academic level? |
                    | **Response Efficiency** | How fast did the model respond, and is the content-to-token ratio efficient? |

                    > **Key Insight:** The RTCACO framework should deliver consistently structured results across *all* tested LLMs,
                    > proving that the prompt architecture—not the specific model—drives academic quality.
                    """)

# ==============================================================================
# TAB 8: About Project
# ==============================================================================
with tabs[7]:
    st.subheader("ℹ️ About AI-Based Academic Content Generator")
    
    st.markdown("""
    ### 1. Problem Statement
    University educators and students frequently spend countless hours manually drafting revision guides, 
    creating balanced multiple-choice diagnostic items, and formulating examination rubrics. While generic LLMs 
    possess vast domain knowledge, unconstrained naive queries yield unstructured, inconsistent, and often 
    superficial outputs unsuitable for rigorous academic assessment.
    
    ### 2. Project Core Objectives & Scope
    This university project was built to perform four explicit prompt engineering milestones:
    - **1. Design Prompts for Notes, Explanations, and Examples:** Implement specialized cognitive scaffolds adapted to diverse academic levels and topics.
    - **2. Compare Outputs for Different Prompt Styles:** Empirically evaluate Zero-Shot, Few-Shot, Role-Based, and RTCACO+CoT prompting paradigms.
    - **3. Optimize Prompts for Clarity and Depth:** Demonstrate iterative prompt engineering (V1 -> V2 -> V3) achieving quantifiable improvements in clarity (+117%), depth (+150%), and hallucination reduction (94%).
    - **4. Document Best Prompt Templates:** Publish a formalized Golden Prompt Library providing standardized, syllabus-aligned templates ready for classroom adoption.

    ### 3. Architecture & RTCACO Prompt Engineering Framework
    The application formats every generation task into six distinct cognitive dimensions:
    - **Role:** Explicit persona assignment (e.g., *Senior Curriculum Architect*, *Lead Psychometrician*).
    - **Task:** Clear educational objective with quantitative boundaries.
    - **Context:** Subject domain, prerequisite benchmarks, and cognitive taxonomy tier.
    - **Audience:** Targeted academic tier (High School to Doctoral) to calibrate terminology and mathematical depth.
    - **Constraints:** Strict anti-hallucination rules, requirement to define terms upon introduction, and mandatory distractor analysis.
    - **Output Format:** Rigid markdown hierarchy guaranteeing deterministic section layout.

    ### 4. Technology Stack
    - **Frontend & Interface:** Streamlit (Python) with custom CSS university styling.
    - **Prompt Framework:** Custom modular RTCACO specification engine (`prompts.py`).
    - **Generation Dispatcher:** Multi-provider handler supporting Demo Mode, Google Gemini REST API, and OpenAI REST API (`generator.py`).
    - **Networking:** Python `requests` for zero-dependency API integration.

    ### 5. Ethical Considerations & System Limitations
    - **Model Limitations:** In Live AI mode, LLMs may produce edge-case inaccuracies. Content should be reviewed by accredited human educators prior to formal summative examinations.
    - **Demo Mode Disclosure:** Demo Mode outputs are clearly labeled as template-driven mock syntheses to maintain absolute academic transparency.
    - **Zero Data Retention:** API keys and generated outputs reside in ephemeral browser session memory and are never persisted or shared.
    """)
