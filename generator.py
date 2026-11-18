"""
generator.py - Academic Content Generation Engine
Supports:
  1. Live AI Generation: Calls Google Gemini or OpenAI REST APIs without external SDK lock-in.
  2. Demo Mode: High-fidelity, clearly-labeled template-based generator.
     Explicitly labeled to never mislead the user.
"""

import json
import hashlib
import logging
import os
import re
import time
from typing import Dict, Any, Tuple
import requests

from prompts import (
    build_study_notes_prompt,
    build_topic_explainer_prompt,
    build_worked_example_prompt,
    build_summary_prompt,
    build_mcq_prompt,
    build_exam_questions_prompt,
)

logger = logging.getLogger(__name__)

_GEMINI_MODEL_CACHE: Dict[str, Tuple[float, list]] = {}
_GEMINI_MODEL_CACHE_TTL_SECONDS = 600


def _gemini_prompt_text(system_prompt: str, user_prompt: str) -> str:
    if system_prompt and system_prompt not in user_prompt:
        return f"Instructions:\n{system_prompt}\n\n{user_prompt}"
    return user_prompt


def _get_gemini_models(api_key: str) -> list:
    key_fingerprint = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    cached = _GEMINI_MODEL_CACHE.get(key_fingerprint)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    base_url = "https://generativelanguage.googleapis.com/v1beta"
    try:
        models_resp = requests.get(
            f"{base_url}/models",
            params={"key": api_key},
            timeout=10
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Could not retrieve available Gemini models: {e}") from e

    if models_resp.status_code != 200:
        raise RuntimeError(
            f"Gemini model discovery failed ({models_resp.status_code}): {models_resp.text}"
        )

    try:
        available_models = models_resp.json().get("models", [])
    except (ValueError, AttributeError) as e:
        raise RuntimeError("Gemini returned an unexpected model-list response.") from e

    supported_models = []
    for model_info in available_models:
        if not isinstance(model_info, dict):
            continue
        name = model_info.get("name")
        methods = model_info.get("supportedGenerationMethods")
        if isinstance(name, str) and isinstance(methods, list) and "generateContent" in methods:
            supported_models.append(name.removeprefix("models/"))
    if not supported_models:
        raise RuntimeError("No Gemini models supporting generateContent are available for this API key.")

    if len(_GEMINI_MODEL_CACHE) >= 32:
        _GEMINI_MODEL_CACHE.pop(next(iter(_GEMINI_MODEL_CACHE)))
    _GEMINI_MODEL_CACHE[key_fingerprint] = (
        time.monotonic() + _GEMINI_MODEL_CACHE_TTL_SECONDS,
        supported_models
    )
    return supported_models


def _select_gemini_text_model(models: list) -> str:
    non_text_markers = ("image", "audio", "tts", "transcribe", "live", "embedding")
    text_models = [
        model for model in models
        if not any(marker in model.lower() for marker in non_text_markers)
    ]
    if not text_models:
        raise RuntimeError("No text-generation Gemini model is available for this API key.")

    flash_models = [model for model in text_models if "flash" in model.lower()]
    model_options = flash_models or text_models
    lite_models = [model for model in model_options if "flash-lite" in model.lower()]
    if lite_models:
        model_options = lite_models

    def model_rank(name: str) -> Tuple[bool, Tuple[int, ...], str]:
        match = re.search(r"gemini-(\d+(?:\.\d+)*)", name)
        version = tuple(int(part) for part in match.group(1).split(".")) if match else ()
        stable = not any(tag in name.lower() for tag in ("preview", "experimental", "-exp"))
        return stable, version, name

    return max(model_options, key=model_rank)


def _gemini_generation_config(model: str) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "maxOutputTokens": 4096,
        "responseModalities": ["TEXT"]
    }
    match = re.search(r"gemini-(\d+)", model.lower())
    if match and int(match.group(1)) >= 3:
        config["thinkingConfig"] = {"thinkingLevel": "LOW"}
    elif model.lower().startswith("gemini-2.5"):
        config["thinkingConfig"] = {"thinkingBudget": 1024}
    else:
        config.update({"temperature": 0.3, "topP": 0.85})
    return config


def _extract_gemini_text(data: Dict[str, Any], model: str) -> str:
    candidates = data.get("candidates", [])
    generated_parts = []
    thought_part_count = 0
    finish_reasons = []
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("finishReason"):
                finish_reasons.append(candidate["finishReason"])
            content = candidate.get("content")
            parts = content.get("parts", []) if isinstance(content, dict) else []
            if not isinstance(parts, list):
                continue
            for part in parts:
                if not isinstance(part, dict):
                    continue
                if part.get("thought"):
                    thought_part_count += 1
                text = part.get("text")
                if isinstance(text, str) and text.strip() and not part.get("thought", False):
                    generated_parts.append(text)
    if generated_parts:
        return "\n".join(generated_parts)

    diagnostics = [f"model: {model}"]
    feedback = data.get("promptFeedback")
    if isinstance(feedback, dict) and feedback.get("blockReason"):
        diagnostics.append(f"prompt block reason: {feedback['blockReason']}")
    if finish_reasons:
        diagnostics.append(f"finish reason: {', '.join(finish_reasons)}")
    if thought_part_count:
        diagnostics.append(f"{thought_part_count} thought-only part(s), but no answer text")
    usage = data.get("usageMetadata")
    if isinstance(usage, dict):
        thought_tokens = usage.get("thoughtsTokenCount")
        if isinstance(thought_tokens, int):
            diagnostics.append(f"thinking tokens: {thought_tokens}")
    if len(diagnostics) == 1:
        diagnostics.append("the response contained no text parts")
    raise RuntimeError(f"Gemini returned no text ({'; '.join(diagnostics)}).")


def call_gemini_api(api_key: str, system_prompt: str, user_prompt: str) -> str:
    """Call a currently available Gemini model using the REST API."""
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    model = _select_gemini_text_model(_get_gemini_models(api_key))
    url = f"{base_url}/models/{model}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [{"text": _gemini_prompt_text(system_prompt, user_prompt)}]
            }
        ],
        "generationConfig": _gemini_generation_config(model)
    }

    try:
        resp = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Gemini API request failed: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API Error ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError("Gemini returned an unexpected generation response.") from e
    if not isinstance(data, dict):
        raise RuntimeError("Gemini returned an unexpected generation response.")

    return _extract_gemini_text(data, model)


def call_openai_api(api_key: str, system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> str:
    """Call OpenAI-compatible REST API using requests."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    raise RuntimeError(f"OpenAI API Error ({resp.status_code}): {resp.text}")


def call_ollama_api(
    system_prompt: str,
    user_prompt: str,
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434"
) -> str:
    """Call a locally running Ollama model without an API key."""
    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=180
        )
    except requests.RequestException as e:
        raise RuntimeError(
            "Could not connect to Ollama at "
            f"{base_url}. Make sure Ollama is installed and running, and that "
            f"the model '{model}' is available. Details: {e}"
        ) from e

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama API Error ({resp.status_code}): {resp.text}")

    try:
        content = resp.json()["message"]["content"]
    except (ValueError, KeyError, TypeError) as e:
        raise RuntimeError("Ollama returned an unexpected response.") from e
    if not content:
        raise RuntimeError("Ollama returned an empty response.")
    return content


def call_gemini_model(api_key: str, system_prompt: str, user_prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    """Call a specific Google Gemini model without requiring system-instruction support."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": _gemini_prompt_text(system_prompt, user_prompt)}]}],
        "generationConfig": _gemini_generation_config(model_name)
    }
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini {model_name} Error ({resp.status_code}): {resp.text}")
    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError(f"Gemini {model_name} returned an unexpected response.") from e
    if not isinstance(data, dict):
        raise RuntimeError(f"Gemini {model_name} returned an unexpected response.")
    return _extract_gemini_text(data, model_name)


# ==============================================================================
# Multi-LLM Comparison Engine
# ==============================================================================

# Registry of all supported LLMs grouped by provider
MULTI_LLM_REGISTRY = {
    "Google Gemini": {
        "key_env": "GEMINI_API_KEY",
        "models": [
            {"id": "gemini-2.0-flash", "display": "Gemini 2.0 Flash", "tier": "Fast & Efficient"},
            {"id": "gemini-1.5-flash", "display": "Gemini 1.5 Flash", "tier": "Balanced"},
            {"id": "gemini-1.5-pro",   "display": "Gemini 1.5 Pro",   "tier": "High Quality"},
        ]
    },
    "OpenAI": {
        "key_env": "OPENAI_API_KEY",
        "models": [
            {"id": "gpt-4o-mini", "display": "GPT-4o Mini",  "tier": "Fast & Cheap"},
            {"id": "gpt-4o",      "display": "GPT-4o",       "tier": "Flagship"},
            {"id": "gpt-4-turbo", "display": "GPT-4 Turbo",  "tier": "High Quality"},
        ]
    }
}


def call_single_llm(provider: str, model_id: str, api_key: str, system_prompt: str, user_prompt: str) -> dict:
    """
    Call a single LLM and return a result dict with output, timing, and status.
    """
    import time
    result = {
        "provider": provider,
        "model_id": model_id,
        "display_name": model_id,
        "output": "",
        "status": "error",
        "time_seconds": 0.0,
        "error": None
    }
    # Find display name
    if provider in MULTI_LLM_REGISTRY:
        for m in MULTI_LLM_REGISTRY[provider]["models"]:
            if m["id"] == model_id:
                result["display_name"] = m["display"]
                break

    start = time.time()
    try:
        if provider == "Google Gemini":
            output = call_gemini_model(api_key, system_prompt, user_prompt, model_name=model_id)
        elif provider == "OpenAI":
            output = call_openai_api(api_key, system_prompt, user_prompt, model=model_id)
        else:
            raise RuntimeError(f"Unknown provider: {provider}")
        result["output"] = output
        result["status"] = "success"
    except Exception as e:
        result["error"] = str(e)
        result["status"] = "error"
    result["time_seconds"] = round(time.time() - start, 2)
    return result


def run_multi_llm_comparison(
    prompt_dict: dict,
    selected_models: list,
    api_keys: dict
) -> list:
    """
    Run the same RTCACO prompt across multiple LLMs and return a list of result dicts.
    selected_models: list of {"provider": str, "model_id": str}
    api_keys: {"Google Gemini": "key...", "OpenAI": "key..."}
    """
    system_instruction = prompt_dict["role"]
    user_message = (
        f"Generate educational content adhering strictly to this prompt specification:\n\n"
        f"{prompt_dict['full_prompt']}"
    )
    results = []
    for sel in selected_models:
        provider = sel["provider"]
        model_id = sel["model_id"]
        key = api_keys.get(provider, "")
        if not key:
            results.append({
                "provider": provider,
                "model_id": model_id,
                "display_name": model_id,
                "output": "",
                "status": "no_key",
                "time_seconds": 0.0,
                "error": f"No API key provided for {provider}"
            })
            continue
        r = call_single_llm(provider, model_id, key, system_instruction, user_message)
        results.append(r)
    return results


# =====================================================================
# High-Quality Demo / Mock Generators (Explicitly Disclosed as Mock)
# =====================================================================

def generate_mock_study_notes(subject: str, topic: str, level: str, difficulty: str, length: str, focus: str = "") -> str:
    focus_str = f" with special focus on *{focus}*" if focus else ""
    return f"""# 📚 Academic Study Notes: {topic}
**Discipline:** {subject} | **Academic Level:** {level} | **Difficulty Tier:** {difficulty} | **Scope:** {length}{focus_str}

---

## 1. Executive Overview & Learning Objectives
This module provides a rigorous conceptual synthesis of **{topic}** within the discipline of **{subject}**. 
By engaging with this unit, students at the **{level}** level will be able to:
1. **Define and contextualize** the foundational axioms and structural taxonomy of {topic}.
2. **Analyze** the operational mechanics, formal representations, and underlying mechanisms.
3. **Differentiate** between standard theoretical approximations and real-world edge scenarios.
4. **Apply** problem-solving frameworks to assess quantitative and qualitative case problems.

---

## 2. Core Definitions & Formal Framework

| Technical Term | Formal Definition | Academic Notation / Synonyms |
| :--- | :--- | :--- |
| **{topic} Core** | The primary operational paradigm governing systematic phenomena in {subject}. | Standard Paradigm (SP) |
| **State Vector / State Space** | The parameterized boundary conditions within which {topic} operations function. | $\\mathcal{{S}} \\subseteq \\mathbb{{R}}^n$ |
| **Equilibrium Condition** | The state where directional driving forces within {topic} reach balanced parity. | $\\sum F_{{net}} = 0$ or $\\Delta H = 0$ |
| **Stochastic Perturbation** | External unmodeled variance influencing stability thresholds. | Noise factor $\\epsilon \\sim \\mathcal{{N}}(0, \\sigma^2)$ |

> **Foundational Axiom:** In {subject}, the behavior of **{topic}** adheres to conservation and deterministic optimization principles under boundary constraints.

---

## 3. In-Depth Conceptual Breakdown & Mechanics

### 3.1 Primary Theoretical Architecture
At the {level} tier, **{topic}** is analyzed through three interdependent pedagogical dimensions:

1. **Structural Ingestion:** How input states, initial configurations, or historical parameters initiate the dynamic cycle.
2. **Transformative Progression:** The internal algorithmic, biochemical, physical, or sociological mechanisms mediating state changes.
3. **Steady-State Attainment:** The convergence towards asymptotic stability or balanced output states.

```
+---------------------+       +-----------------------+       +---------------------+
|   Initial Inputs    | ----> | Core Transformations  | ----> |  Empirical Outputs  |
|  Boundary & States  |       | ({topic} Dynamics)    |       | Measured Outcomes   |
+---------------------+       +-----------------------+       +---------------------+
                                          |
                              [Feedback Loop / Error Check]
```

### 3.2 Formal Mathematical / Logical Formulation
For formal evaluation in {subject}:
$$f({topic}) = \\int_{{t_0}}^{{t_1}} \\Psi(x, t) \\cdot \\nabla \\Phi(x) \\, dt + \\Omega_{{boundary}}$$

Where:
- $\\Psi(x, t)$ describes the density distribution of core variables over time.
- $\\nabla \\Phi(x)$ designates the potential field gradient dictating rate of change.
- $\\Omega_{{boundary}}$ accounts for institutional, empirical, or physical limits.

---

## 4. Illustrative Worked Example & Case Study

### Context: Applied Scenario in {subject}
Consider an empirical benchmark where a system governed by **{topic}** encounters a 25% surge in external load.

- **Initial State ($S_0$):** Baseline throughput operating under nominal steady-state.
- **Intervention / Disturbance:** Dynamic impulse applied over interval $\\Delta t$.
- **Analytical Solution:**
  1. Calculate initial flux using standard conservation relations.
  2. Map the phase transition boundary to determine if bifurcation thresholds are crossed.
  3. Validate that dissipative loss matches empirical theoretical bounds.
- **Pedagogical Takeaway:** Systems exhibiting **{topic}** characteristics demonstrate resilience up to the critical damping ratio, beyond which non-linear divergence occurs.

---

## 5. Common Misconceptions & Academic Nuances

- ❌ **Misconception 1:** Assuming that {topic} operates independently of surrounding system parameters.
  - *Correction:* In modern {subject} literature, {topic} is intrinsically coupled with feedback loops and environmental context.
- ❌ **Misconception 2:** Equating conceptual simplicity at introductory levels with triviality in real-world implementations.
  - *Correction:* Edge cases introduce stochastic uncertainty that invalidates naive linear models.

---

## 6. Active Recall & Self-Assessment Checkpoints

1. **Divergence Test:** Under what specific thermodynamic, computational, or theoretical conditions will the standard model of {topic} fail?
2. **Comparative Challenge:** How does {topic} contrast fundamentally with its historical or counter-paradigm counterpart in {subject}?
3. **Application Problem:** Design a brief experimental protocol to measure the rate-limiting step when evaluating {topic}.
"""


def generate_mock_topic_explainer(subject: str, topic: str, level: str, difficulty: str, length: str, focus: str = "") -> str:
    return f"""# 💡 Demystifying: {topic}
**Subject:** {subject} | **Target Audience:** {level} Students | **Tone:** Intuitive, Rigorous, Conceptual

---

## 1. The 30-Second Elevator Pitch
If you were explaining **{topic}** over coffee, here is what you would say:
> Imagine you have a complex system where every part wants to pull in its own direction. **{topic}** is the invisible ruleset, conductor, or mechanism that keeps everything running synchronously without collapsing into total chaos.

In {subject}, {topic} solves the fundamental dilemma of **how to coordinate complex interactions reliably without manual micromanagement**.

---

## 2. The Mental Model / Analogy: The Intelligent Traffic Roundabout
Instead of thinking about **{topic}** as abstract equations or dry textbook definitions, picture a **busy modern roundabout in a metropolitan city**:

- **Without {topic} (Traditional / Naive State):** You have individual traffic lights at every lane. If one sensor misbehaves, traffic jams cascade for miles, causing bottlenecks.
- **With {topic} (Optimized Coordination):** Incoming cars yield dynamically to circulating traffic. Velocity, gap size, and momentum dictate the flow. 
- **The Lesson:** {topic} acts like that roundabout—a self-regulating architecture that balances supply, demand, and stability organically.

---

## 3. Step-by-Step Mechanical Breakdown

```
[Phase 1: Detection] ---> [Phase 2: Evaluation] ---> [Phase 3: Execution] ---> [Phase 4: Feedback]
```

1. **Step 1 - Signal Sensing / Input Ingestion:**
   The system registers environmental changes, numerical vectors, or structural signals relevant to {topic}.
2. **Step 2 - Boundary Evaluation:**
   Pre-programmed or physical constraints dictate whether action is triggered (thresholding mechanism).
3. **Step 3 - Dynamic Adjustment:**
   The core transformation of {topic} executes, redistributing energy, computational cycles, capital, or biological mass.
4. **Step 4 - Convergence & Validation:**
   The output is checked against equilibrium metrics to guarantee systemic stability.

---

## 4. Real-World Applications & Why It Matters
- **Industrial & Technological Impact:** Engineers, researchers, and practitioners in {subject} leverage {topic} to build fault-tolerant, scalable architectures.
- **Academic Relevance:** Mastery of this concept unlocks advanced literature in higher-level {level} coursework.
- **Everyday Parallels:** From natural ecosystems to distributed computational servers, {topic} principles govern efficiency everywhere.

---

## 5. The Golden Rule to Remember
> **If you remember nothing else:** {topic} is fundamentally about **balancing efficiency with systemic stability**. When pushed beyond threshold constraints, the system always sacrifices efficiency to protect structural integrity.
"""


def generate_mock_worked_example(subject: str, topic: str, level: str, difficulty: str, length: str, focus: str = "") -> str:
    return f"""# 🧪 Pedagogical Worked Example: {topic}
**Subject:** {subject} | **Benchmark Tier:** {level} | **Difficulty:** {difficulty} | **Focus:** Step-by-Step Resolution

---

## 1. Problem Statement & Boundary Conditions
A quantitative system governed by the foundational laws of **{topic}** in **{subject}** operates under the following calibrated initial parameters:

- **State Parameter ($x_0$):** $12.5$ standard normalized units.
- **Driving Potential ($P_{{drive}}$):** $4.8 \\times 10^3 \\text{ J/mol}$ or $\\text{V/m}$.
- **Impedance / Drag Coefficient ($\\gamma$):** $0.18 \\text{ s}^{-1}$.
- **Operational Boundary Constraints:** The variable $x(t)$ must strictly remain within the stability zone $[0, 50]$.

**Objective:** Compute the transient state response at $t = 2.0\\text{ s}$, evaluate whether boundary limits are preserved, and determine total dissipative loss.

---

## 2. Theoretical Framing & Governing Equations
To solve this benchmark problem, we apply the canonical relaxation formula in {subject}:

$$x(t) = x_{{\\infty}} + (x_0 - x_{{\\infty}}) \\cdot e^{{-\\gamma t}}$$

Where the asymptotic equilibrium state is given by:
$$x_{{\\infty}} = \\frac{{P_{{drive}}}}{{\\kappa \\cdot \\gamma}} = 35.0 \\text{ units}$$

---

## 3. Step-by-Step Analytical Resolution

### Step 1: Substitute Initial Values into Boundary Equation
Substitute $x_0 = 12.5$, $x_{{\\infty}} = 35.0$, $\\gamma = 0.18$, and $t = 2.0$:
$$x(2.0) = 35.0 + (12.5 - 35.0) \\cdot e^{{-(0.18)(2.0)}}$$

### Step 2: Compute Exponential Decay Factor
$$e^{{-0.36}} \\approx 0.6977$$

### Step 3: Evaluate State Displacement
$$(12.5 - 35.0) = -22.5$$
$$-22.5 \\times 0.6977 \\approx -15.70$$

### Step 4: Final State Determination
$$x(2.0) = 35.0 - 15.70 = 19.30 \\text{ units}$$

---

## 4. Verification & Sanity Checks
- ✅ **Dimensional Consistency:** All terms reduce cleanly to normalized state units.
- ✅ **Monotonicity Check:** Since $x_0 (12.5) < x_{{\\infty}} (35.0)$, the state must monotonically increase over time. $19.30 > 12.5$, satisfying physical directionality.
- ✅ **Boundary Verification:** $19.30 \\in [0, 50]$, confirming zero boundary violations.

---

## 5. Common Student Pitfalls & Diagnostic Analysis
- ⚠️ **Pitfall 1 (Sign Error):** Inverting $(x_0 - x_{{\\infty}})$ to $(x_{{\\infty}} - x_0)$, resulting in unphysical divergence.
- ⚠️ **Pitfall 2 (Unit Mismatch):** Failing to convert time constants into SI seconds before calculating the exponent $\\gamma t$.
- ⚠️ **Pitfall 3 (Ignoring Boundary Envelopes):** Forgetting to verify whether the intermediate trajectory breaches the upper bound threshold.

---

## 6. Generalization Rule & Takeaway
> **Core Principle:** Whenever analyzing **{topic}** in {subject}, always identify whether the system is under-damped, critically damped, or over-damped before executing numerical derivations. The decay envelope dictates long-term stability.
"""


def generate_mock_summary(subject: str, topic: str, level: str, difficulty: str, length: str, focus: str = "") -> str:
    return f"""# 📝 High-Yield Revision Summary: {topic}
**Subject:** {subject} | **Exam Level:** {level} | **Review Mode:** Quick Revision Sheet

---

## 1. 60-Second Rapid Synthesis
**{topic}** is a core pillar in **{subject}**. At the {level} standard, students must grasp:
- The fundamental governing mechanism and its primary variables.
- How input variations propagate through the operational pipeline.
- Diagnostic criteria for identifying system equilibrium versus failure modes.

---

## 2. Core Pillars & Principles (Digest)
- 🔹 **Pillar 1 (Invariant Foundation):** Conservation laws or baseline invariances dictate standard behavior.
- 🔹 **Pillar 2 (Causal Drivers):** Gradients (temperature, potential, cost functions, or incentives) determine vector directionality.
- 🔹 **Pillar 3 (Limiting Factors):** Performance is bound by the weakest link / rate-limiting bottleneck.
- 🔹 **Pillar 4 (Dynamic Feedback):** Negative feedback promotes stabilization; positive feedback accelerates escalation.

---

## 3. High-Yield Comparative Matrix

| Attribute | Elementary View | Advanced {level} View ({topic}) |
| :--- | :--- | :--- |
| **Primary Focus** | Isolated component behavior | Holistic coupled interactions |
| **System Model** | Linear, deterministic approximation | Non-linear, constrained optimization |
| **Sensitivity** | Assumes static environment | Accounts for dynamic environmental perturbations |
| **Assessment Focus** | Rote recall of definition | Analytical troubleshooting and rubric application |

---

## 4. Flashcard Terminology (Instant Memory Triggers)

- 🗂️ **Term A:** *Canonical State* $\\rightarrow$ Standard baseline configuration prior to stress testing.
- 🗂️ **Term B:** *Threshold Inversion* $\\rightarrow$ The transition point where system efficiency begins degrading.
- 🗂️ **Term C:** *Dynamic Coupling* $\\rightarrow$ Interdependence where variable $X$ directly modulates response curve $Y$.

---

## 5. High-Stakes Exam Trap Alerts ⚠️
1. **Trap 1:** Forgetting to state units or boundary dimensions when defining variables in {topic}.
2. **Trap 2:** Confusing *correlation* between factors with the direct causal driver of {topic}.
3. **Trap 3:** Applying standard equilibrium equations during non-steady-state transient periods.
"""


def generate_mock_mcqs(subject: str, topic: str, level: str, difficulty: str, length: str, focus: str = "") -> str:
    return f"""# 🎯 Multiple-Choice Assessment: {topic}
**Subject:** {subject} | **Level:** {level} | **Standard:** Psychometrically Calibrated ({difficulty})

---

### Question 1
**In the context of {subject}, which of the following best characterizes the primary function of {topic}?**
- [ ] A) It serves solely as an emergency fail-safe with zero role during normal steady-state operation.
- [x] B) It governs the equilibrium dynamics and regulates state transitions under bounded constraints.
- [ ] C) It eliminates all entropy, external interference, and operational variance completely.
- [ ] D) It operates entirely at random without deterministic mathematical or physical underpinnings.

**Correct Answer:** **B**
- **Pedagogical Rationale:** Option B accurately captures the consensus academic definition in {subject}. {topic} is continuous and regulatory, functioning to balance systemic forces within well-defined parameters.
- **Distractor Analysis:**
  - *Option A is incorrect* because it limits the mechanism to emergency protocols rather than baseline function.
  - *Option C is incorrect* because no practical system eliminates entropy or variance in totality.
  - *Option D is incorrect* because systems in {subject} adhere to structured stochastic or deterministic laws.

---

### Question 2
**When the primary driving gradient of {topic} is halved while boundary resistance remains constant, what is the theoretical consequence?**
- [ ] A) The throughput instantaneously quadruples due to inverse square dynamics.
- [x] B) The net transformation rate decreases proportionally, leading to an extended relaxation time.
- [ ] C) System equilibrium transitions irreversibly into chaotic turbulence.
- [ ] D) No observable change occurs because {topic} is invariant to driving gradients.

**Correct Answer:** **B**
- **Pedagogical Rationale:** In standard {subject} modeling, rate is directly proportional to driving force across linear regimes. Halving the gradient halves throughput and extends time to equilibrium.
- **Distractor Analysis:**
  - *Option A confuses* inverse square dilution with direct potential differences.
  - *Option C suggests* chaotic catastrophe, which only occurs under extreme non-linear forcing.
  - *Option D denies* foundational conservation laws.

---

### Question 3
**Which of the following conditions constitutes an essential prerequisite for validly modeling {topic} at the {level} tier?**
- [ ] A) The assumption of zero temperature and frictionless media at all times.
- [ ] B) Completely unconstrained infinite resource availability.
- [x] C) Well-defined initial boundary conditions and verifiable conservation parameters.
- [ ] D) Disregard for empirical validation in favor of speculative heuristic rules.

**Correct Answer:** **C**
- **Pedagogical Rationale:** Every analytical framework in {subject} requires calibrated initial boundary states to yield solvable, verifiable outcomes.
- **Distractor Analysis:**
  - *Options A & B* are unphysical over-idealizations unsuitable for rigorous {level} curricula.
  - *Option D* violates scientific method requirements.

---

### Question 4
**A student researcher analyzes an anomaly where {topic} fails to converge to its predicted steady-state. Which diagnostic step should be conducted first?**
- [x] A) Verify the integrity of sensor inputs and test for unmodeled feedback leakage across boundary conditions.
- [ ] B) Immediately discard the foundational theories of {subject} as obsolete.
- [ ] C) Increase external voltage or load by 1000% to force brute-force convergence.
- [ ] D) Alter empirical data points to artificially match textbook curves.

**Correct Answer:** **A**
- **Pedagogical Rationale:** Sound scientific inquiry begins with boundary and calibration verification before questioning axiomatic theory or altering raw observations.
- **Distractor Analysis:**
  - *Option B* is an anti-scientific overreaction.
  - *Option C* risks physical damage or numerical divergence.
  - *Option D* represents scientific misconduct.

---

### Question 5
**How does {topic} scale when the operational dimensions of the host system increase by an order of magnitude?**
- [ ] A) It remains exactly identical regardless of surface-area-to-volume ratio changes.
- [ ] B) It vanishes completely due to dimensional decoupling.
- [x] C) It exhibits non-linear scaling effects, often requiring modular partitioning or secondary dissipation mechanisms.
- [ ] D) It converts spontaneously into an unrelated thermodynamic phenomenon.

**Correct Answer:** **C**
- **Pedagogical Rationale:** Scaling in {subject} is rarely linear. As volume scales cubically while surface area scales quadratically, rate-limiting dissipation factors impose non-linear constraints on {topic}.
"""


def generate_mock_exam_questions(subject: str, topic: str, level: str, difficulty: str, length: str, focus: str = "") -> str:
    return f"""# ✍️ University Examination Paper: {topic}
**Department:** {subject} | **Course Level:** {level} | **Assessment Type:** Summative Exam Section
**Time Allocated:** 60 Minutes | **Total Marks:** 40 Marks

---

## SECTION A: Short-Answer Conceptual Questions (15 Marks)
*Answer all three questions in this section. Concise, precise answers are required.*

### Question 1 (5 Marks)
**State the primary governing principle of {topic} and identify two critical boundary assumptions required for its application.**
- **Suggested Time:** 8 minutes.
- **Model Answer Key:**
  1. *Definition & Principle (2 Marks):* Candidate accurately defines {topic} as the systematic mechanism regulating state transitions in {subject}.
  2. *Boundary Assumptions (2 Marks):* Candidate identifies two valid constraints (e.g., closed system conservation, steady-state approximation, or bounded noise).
  3. *Academic Notation & Clarity (1 Mark):* Appropriate domain terminology utilized without ambiguity.

### Question 2 (5 Marks)
**Distinguish between static equilibrium and dynamic steady-state in the context of {topic}.**
- **Suggested Time:** 8 minutes.
- **Model Answer Key:**
  1. *Static Equilibrium (2 Marks):* State where opposing forward and reverse driving potentials are zero ($v = 0$).
  2. *Dynamic Steady-State (2 Marks):* State where continuous flux exists, but concentration/energy profiles remain constant over time ($dC/dt = 0$).
  3. *Contextual Example (1 Mark):* Illustrative case in {subject} correctly cited.

### Question 3 (5 Marks)
**Explain why naive linear models often fail when predicting the performance of {topic} under extreme stress conditions.**
- **Suggested Time:** 8 minutes.
- **Model Answer Key:**
  1. *Mechanism of Breakdown (3 Marks):* Identification of non-linear saturation, resource depletion, or phase changes occurring at stress thresholds.
  2. *Mathematical / Empirical Justification (2 Marks):* Reference to higher-order differential terms or empirical limits.

---

## SECTION B: Long-Answer Analytical & Synthesis Questions (25 Marks)
*Answer both questions. Structured arguments, diagrams, and step-by-step reasoning are required.*

### Question 4: Analytical Derivation & Case Analysis (12 Marks)
**An industrial research team observes unexpected oscillation during a pilot test of {topic}. Formulate a complete diagnostic framework to identify whether this is driven by internal positive feedback or external phase lag.**

- **Marking Scheme:**
  - **Part I: Theoretical Framing (3 Marks):** Mathematical or formal articulation of transfer functions or stability criteria.
  - **Part II: Diagnostic Protocol (4 Marks):** Step-by-step experimental method to isolate external noise from endogenous dynamics.
  - **Part III: Mitigation Architecture (3 Marks):** Proposed damping, control loops, or systemic interventions.
  - **Part IV: Risk Analysis & Rigor (2 Marks):** Evaluation of edge-case failure modes.

### Question 5: Applied System Design & Critical Evaluation (13 Marks)
**Synthesize a proposed modern redesign for a legacy {subject} system utilizing the advanced principles of {topic}. Defend your architectural choices against trade-offs in efficiency, scalability, and implementation cost.**

- **Marking Scheme:**
  - **Problem Decomposition (3 Marks):** Clear analysis of legacy vulnerabilities.
  - **Proposed Architecture (4 Marks):** Rigorous, evidence-backed integration of {topic}.
  - **Trade-off Matrix (4 Marks):** Thorough critical analysis comparing throughput vs. stability.
  - **Conclusion & Scholarly Synthesis (2 Marks):** Coherent, logically structured defense suitable for a {level} defense.
"""


def generate_content(
    content_type: str,
    subject: str,
    topic: str,
    level: str,
    difficulty: str,
    length: str,
    focus: str = "",
    api_provider: str = "Demo Mode",
    api_key: str = "",
    api_model: str = "llama3.2:3b"
) -> Tuple[str, str, Dict[str, str]]:
    """
    Unified generator dispatcher.
    Returns: (output_markdown, mode_label, prompt_dict)
    """
    # 1. Build the engineered prompt
    if content_type == "Study Notes":
        prompt_dict = build_study_notes_prompt(subject, topic, level, difficulty, length, focus)
        mock_fn = generate_mock_study_notes
    elif content_type == "Topic Explainer":
        prompt_dict = build_topic_explainer_prompt(subject, topic, level, difficulty, length, focus)
        mock_fn = generate_mock_topic_explainer
    elif content_type == "Worked Examples":
        prompt_dict = build_worked_example_prompt(subject, topic, level, difficulty, length, focus)
        mock_fn = generate_mock_worked_example
    elif content_type == "Summary":
        prompt_dict = build_summary_prompt(subject, topic, level, difficulty, length, focus)
        mock_fn = generate_mock_summary
    elif content_type == "Multiple-Choice Questions":
        prompt_dict = build_mcq_prompt(subject, topic, level, difficulty, length, focus)
        mock_fn = generate_mock_mcqs
    elif content_type == "Exam Questions":
        prompt_dict = build_exam_questions_prompt(subject, topic, level, difficulty, length, focus)
        mock_fn = generate_mock_exam_questions
    else:
        prompt_dict = build_study_notes_prompt(subject, topic, level, difficulty, length, focus)
        mock_fn = generate_mock_study_notes

    # Check for environment variables if api_key not directly supplied
    if not api_key:
        if api_provider == "Google Gemini":
            api_key = os.environ.get("GEMINI_API_KEY", "")
        elif api_provider == "OpenAI":
            api_key = os.environ.get("OPENAI_API_KEY", "")

    # 2. Check if genuine AI generation is enabled
    if api_provider == "Ollama":
        system_instruction = prompt_dict["role"]
        user_message = (
            f"Generate educational content adhering strictly to this prompt specification:\n\n"
            f"{prompt_dict['full_prompt']}"
        )
        try:
            content = call_ollama_api(system_instruction, user_message, model=api_model)
            mode_label = f"🟢 Local AI Generation (Ollama | {api_model})"
            return content, mode_label, prompt_dict
        except RuntimeError:
            logger.exception("Ollama generation failed; using the demo template.")
            fallback_content = mock_fn(subject, topic, level, difficulty, length, focus)
            mode_label = "🟡 Demo Mode (Ollama Error Fallback - Pre-computed Pedagogical Template)"
            return fallback_content, mode_label, prompt_dict

    if api_provider != "Demo Mode" and api_key.strip():
        system_instruction = prompt_dict["role"]
        user_message = (
            f"Generate educational content adhering strictly to this prompt specification:\n\n"
            f"{prompt_dict['full_prompt']}"
        )
        try:
            if api_provider == "Google Gemini":
                content = call_gemini_api(api_key.strip(), system_instruction, user_message)
                mode_label = f"🟢 Live AI Generation (Google Gemini | Key Verified)"
                return content, mode_label, prompt_dict
            elif api_provider == "OpenAI":
                content = call_openai_api(api_key.strip(), system_instruction, user_message)
                mode_label = f"🟢 Live AI Generation (OpenAI GPT-4o-mini | Key Verified)"
                return content, mode_label, prompt_dict
        except Exception as e:
            # Explicitly report the error and fail gracefully or fallback with clear disclosure
            error_notice = f"> ⚠️ **Live AI Generation Error:** {str(e)}\n\n*Falling back to clearly labeled Demo Mode below.*"
            fallback_content = mock_fn(subject, topic, level, difficulty, length, focus)
            mode_label = "🟡 Demo Mode (API Error Fallback - Pre-computed Pedagogical Template)"
            return f"{error_notice}\n\n---\n\n{fallback_content}", mode_label, prompt_dict

    # 3. Default Demo Mode (Guaranteed to work without any API key)
    mode_label = "🔵 Demo Mode (High-Fidelity Pedagogical Template - No API Key Required)"
    content = mock_fn(subject, topic, level, difficulty, length, focus)
    return content, mode_label, prompt_dict
