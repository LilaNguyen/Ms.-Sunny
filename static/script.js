const INITIAL_QUESTION = "What sound does the letter C make? Give an example word!";
let currentQuestion = INITIAL_QUESTION;

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showLoading(show) {
  const btn = document.getElementById("submit-btn");
  const indicator = document.getElementById("loading-indicator");
  const logsDiv = document.getElementById("thinking-logs");

  if (show) {
    btn.disabled = true;
    btn.innerHTML = '⏳ Thinking...';
    indicator.classList.remove("hidden");
    logsDiv.innerHTML = "";
  } else {
    btn.disabled = false;
    btn.innerHTML = '🚀 Submit Answer!';
    indicator.classList.add("hidden");
  }
}

function renderReasoningLogs(logs) {
  const logsDiv = document.getElementById("thinking-logs");
  logsDiv.innerHTML = "";

  if (!logs || logs.length === 0) {
    logsDiv.innerHTML = `<div class="thinking-placeholder">💭 Nemotron reasoning complete.</div>`;
    return;
  }

  logs.forEach((log, index) => {
    const logCard = document.createElement("div");
    logCard.className = "log-card";

    const steps = ["THOUGHT", "ACTION", "OBSERVATION", "PLAN"];
    const innerHTML = steps
      .filter((step) => log[step])
      .map(
        (step) =>
          `<div class="log-step">
             <strong>${step}:</strong> ${escapeHtml(log[step])}
           </div>`
      )
      .join("");

    logCard.innerHTML = `<div class="log-agent">Agent ${index + 1}</div>${innerHTML}`;
    logsDiv.appendChild(logCard);
  });
}

function updateQuestion(question) {
  currentQuestion = question;
  const questionEl = document.getElementById("question-text");
  if (questionEl) questionEl.textContent = question;
}

function updateSpeechBubble(text) {
  const bubble = document.getElementById("speech-text");
  if (bubble) bubble.innerHTML = text;
}

function showResult(isCorrect, explanation) {
  const resultCard = document.getElementById("result-card");
  if (!resultCard) return;

  resultCard.classList.remove("correct", "incorrect", "hidden");

  if (isCorrect) {
    resultCard.classList.add("correct");
    resultCard.innerHTML = `🌟 Awesome work! ${escapeHtml(explanation) || ""}`;
  } else {
    resultCard.classList.add("incorrect");
    resultCard.innerHTML = `💪 Good try! ${escapeHtml(explanation) || ""}`;
  }
}

async function submitAnswer() {
  const answerInput = document.getElementById("answer-input");
  const answer = answerInput?.value.trim();

  if (!answer) {
    if (answerInput) answerInput.focus();
    return;
  }

  showLoading(true);

  try {
    const response = await fetch("/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: currentQuestion,
        answer: answer,
      }),
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.error || `Server error: ${response.status}`);
    }

    const data = await response.json();

    renderReasoningLogs(data.reasoning_logs || []);
    showResult(data.is_correct, data.explanation);

    const gapsText =
      data.learning_gaps && data.learning_gaps.length > 0
        ? `We can work on: ${data.learning_gaps.join(", ")}. `
        : "";

    updateSpeechBubble(
      data.is_correct
        ? `🌟 You're a star! Great job!`
        : `💪 Good effort! ${gapsText}Check the explanation below and try the next question!`
    );

    if (data.next_question) {
      setTimeout(() => {
        updateQuestion(data.next_question);
        if (answerInput) answerInput.value = "";
        if (answerInput) answerInput.focus();
      }, 1500);
    }

    // Display which model produced the reasoning
    const modelStatus = document.getElementById("model-status");
    if (modelStatus) modelStatus.innerHTML = `⚡ Powered by ${escapeHtml(data.model || "NVIDIA Nemotron")}`;

  } catch (error) {
    renderReasoningLogs([]);
    const logsDiv = document.getElementById("thinking-logs");
    if (logsDiv)
      logsDiv.innerHTML = `<div class="thinking-placeholder">⚠️ Error: ${escapeHtml(
        error.message
      )}</div>`;
    updateSpeechBubble(`😅 Something went wrong. Check that the NVIDIA API key is set correctly.`);
  } finally {
    showLoading(false);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const answerInput = document.getElementById("answer-input");
  if (answerInput) {
    answerInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        submitAnswer();
      }
    });
  }

  const submitBtn = document.getElementById("submit-btn");
  if (submitBtn) submitBtn.addEventListener("click", submitAnswer);
});