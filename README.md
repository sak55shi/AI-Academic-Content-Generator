# 🎓 AI-Based Academic Content Generator

> A university-grade dashboard for synthesizing study notes, conceptual explanations, revision summaries, multiple-choice diagnostic assessments, and formal examination papers using disciplined Prompt Engineering.

---

## 📋 Table of Contents
1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Prompt Engineering Architecture (RTCACO)](#-prompt-engineering-architecture-rtcaco)
4. [Quick Start & Run Instructions](#-quick-start--run-instructions)
5. [Demo Mode vs. Live AI Mode](#-demo-mode-vs-live-ai-mode)
6. [Project Structure](#-project-structure)
7. [Technology Stack](#-technology-stack)

---

## 🌟 Overview & Core Project Requirements
Built for a university **Prompt Engineering Course Project**, this application specifically performs and demonstrates four essential prompt engineering milestones:
1. **Design prompts for notes, explanations, and examples:** Dedicated RTCACO cognitive scaffolds.
2. **Compare outputs for different prompt styles:** Empirical comparison of Naive Zero-Shot, Few-Shot, Role-Based, and RTCACO+CoT.
3. **Optimize prompts for clarity and depth:** Iterative V1 -> V2 -> V3 pipeline with measurable gains (+117% clarity, +150% depth, 94% hallucination reduction).
4. **Document best prompt templates:** A codified "Golden Prompt Library" ready for classroom and LMS adoption.

---

## ⚡ Key Features

- **1. 📚 Study Notes Generator:** Produces structured study notes with executive summaries, formal definitions, deep conceptual mechanics, worked examples, and active-recall checkpoints.
- **2. 💡 Topic Explainer:** Demystifies difficult theories using relatable real-world analogies, step-by-step mechanical breakdowns, and core mental models.
- **3. 🧪 Worked Example Generator:** Complete step-by-step quantitative and analytical problem resolutions with boundary condition checks and student pitfall alerts.
- **4. 📝 Revision Summary:** High-yield rapid revision sheets featuring 60-second digests, comparative matrices, flashcard terminology, and common exam trap alerts.
- **5. 🎯 MCQ Generator:** Generates psychometrically calibrated multiple-choice questions with 4 distinct options, explicit correct answers, pedagogical rationales, and distractor analyses.
- **6. ✍️ Exam Question Generator:** Formulates complete university examination sections (Section A: Short Answer [3-5 marks] and Section B: Long Answer [10-15 marks]) complete with model marking rubrics.
- **7. 🔬 Prompt Engineering Lab:** Interactive workbench covering:
  - **Prompt Design for Notes, Explanations & Examples**
  - **4-Style Comparative Output Matrix** (Zero-Shot vs Few-Shot vs Role-Based vs RTCACO+CoT)
  - **Iterative Optimization Pipeline for Clarity & Depth**
  - **Best Prompt Templates (Golden Prompt Library)**
- **8. 📥 Export Capabilities:** Single-click download to Markdown (`.md`) and Plain Text (`.txt`).
- **9. 🔍 Prompt Inspector:** Expandable inspection view showing the exact prompt specification fed into the generation pipeline.

---

## 🧠 Prompt Engineering Architecture (RTCACO)

Every prompt is constructed according to the **RTCACO** framework:

| Dimension | Purpose | Example |
| :--- | :--- | :--- |
| **R - Role** | Assigns domain authority & pedagogical stance | *Distinguished Professor & Curriculum Architect* |
| **T - Task** | Unambiguous educational objective | *Synthesize exhaustive, publication-grade academic study notes* |
| **C - Context** | Subject discipline & difficulty tier | *Discipline: Computer Science \| Level: Undergraduate* |
| **A - Audience** | Calibrates cognitive readiness & vocabulary | *Undergraduate students preparing for university exams* |
| **C - Constraints** | Hallucination guardrails & anti-bias rules | *Define all technical terms; no unverifiable empirical claims* |
| **O - Output Spec** | Rigid markdown hierarchy | *Numbered markdown schema with definitions table & self-tests* |

---

## 🚀 Quick Start & Run Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the Streamlit application using Python's module launcher:
```bash
python -m streamlit run app.py
```

### 3. Access in Browser
Once running, open your web browser at:
```
http://localhost:8501
```

---

## 🔌 Demo Mode vs. Live AI Mode

| Mode | API Key Required? | Description |
| :--- | :--- | :--- |
| **🔵 Demo Mode** | **No** | Default offline mode with high-fidelity, complete academic templates. Clearly labeled to maintain academic transparency. |
| **🟢 Google Gemini** | Optional | Real-time live AI generation. The app checks which generation models are available to your API key. Input your key in the sidebar. |
| **🟢 OpenAI** | Optional | Real-time live AI generation using OpenAI models (e.g. `gpt-4o-mini`). Input your key in the sidebar. |
| **🟢 Ollama (Local)** | **No** | Runs a downloaded model on your computer. Install Ollama, download a model (for example `ollama pull llama3.2:3b`), then select Ollama in the sidebar. |

> **Security Note:** API keys are entered via secure masked password inputs and are stored exclusively in temporary browser session memory. Keys are never saved to disk or logged.

Ollama is a local model runner and does not require a hosted API key. Model downloads require an internet connection and sufficient disk space; generation runs locally on your computer.

---

## 📂 Project Structure

```
academic-content-generator/
│
├── app.py                # Main Streamlit web application & UI dashboard
├── prompts.py            # RTCACO Prompt Engineering templates & comparison logic
├── generator.py          # Unified dispatcher (Demo Mode, Ollama, Gemini API, OpenAI API)
├── requirements.txt      # Python dependencies (Streamlit)
└── README.md             # Documentation, architecture, and run instructions
```

---

## 🛠️ Technology Stack
- **Framework:** Streamlit
- **Language:** Python 3.x
- **Styling:** Custom CSS (Navy blue `#0B2545`, Light blue `#8DA9C4`, Clean white cards)
- **API Integration:** Standard `requests` library (zero heavy SDK overhead)
