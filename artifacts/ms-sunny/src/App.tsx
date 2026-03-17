import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const C = {
  bg: "oklch(0.95 0.02 230)",
  card: "oklch(1 0 0)",
  coral: "oklch(0.72 0.16 25)",
  coralDark: "oklch(0.60 0.16 25)",
  sky: "oklch(0.85 0.1 230)",
  skyDark: "oklch(0.70 0.12 230)",
  yellow: "oklch(0.90 0.18 90)",
  green: "oklch(0.75 0.18 145)",
  greenDark: "oklch(0.62 0.18 145)",
  pink: "oklch(0.88 0.1 350)",
  muted: "oklch(0.45 0.05 250)",
  text: "oklch(0.25 0.05 250)",
  border: "oklch(0.88 0.04 230)",
};

interface Choice { word: string; emoji: string; }

interface ReasoningLog {
  agent: string;
  THOUGHT: string;
  ACTION: string;
  OBSERVATION: string;
  PLAN: string;
}

interface AnswerResponse {
  is_correct: boolean;
  explanation: string;
  next_question: string;
  learning_gaps: string[];
  reasoning_logs: ReasoningLog[];
  choices: Choice[];
  current_letter: string | null;
  error?: string;
}

interface QuestionState {
  question: string;
  current_letter: string | null;
  choices: Choice[];
}

function LetterCard({ letter, emoji = "🌟" }: { letter: string; emoji?: string }) {
  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.8, opacity: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      style={{ position: "relative", display: "inline-block" }}
    >
      <div style={{
        background: C.card,
        borderRadius: "2rem",
        boxShadow: "0 12px 40px rgba(0,0,0,0.18)",
        padding: "2rem 2.5rem",
        border: `4px solid ${C.sky}`,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        minWidth: 160,
      }}>
        <motion.div
          style={{ position: "absolute", top: -16, right: -16, fontSize: "2rem", zIndex: 2 }}
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
        >
          {emoji}
        </motion.div>
        <motion.div
          style={{
            fontSize: "clamp(5rem, 14vw, 10rem)",
            fontWeight: 900,
            color: C.coral,
            lineHeight: 1,
            fontFamily: "'Nunito', sans-serif",
            userSelect: "none",
          }}
          animate={{ scale: [1, 1.06, 1] }}
          transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
        >
          {letter}
        </motion.div>
      </div>
    </motion.div>
  );
}

function MultipleChoice({
  choices,
  onSelect,
  disabled,
  selected,
}: {
  choices: Choice[];
  onSelect: (word: string) => void;
  disabled: boolean;
  selected: string | null;
}) {
  const CARD_COLORS = [
    { bg: "oklch(0.96 0.05 85)", border: C.yellow, hover: "oklch(0.90 0.10 85)" },
    { bg: "oklch(0.96 0.04 145)", border: C.green, hover: "oklch(0.90 0.09 145)" },
    { bg: "oklch(0.96 0.04 230)", border: C.sky, hover: "oklch(0.90 0.08 230)" },
    { bg: "oklch(0.96 0.04 350)", border: C.pink, hover: "oklch(0.90 0.08 350)" },
  ];

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 14,
    }}>
      {choices.map((choice, i) => {
        const col = CARD_COLORS[i % CARD_COLORS.length];
        const isSelected = selected === choice.word;
        return (
          <motion.button
            key={choice.word}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07, type: "spring", stiffness: 280, damping: 22 }}
            whileHover={disabled ? {} : { scale: 1.04, y: -2 }}
            whileTap={disabled ? {} : { scale: 0.96 }}
            onClick={() => !disabled && onSelect(choice.word)}
            disabled={disabled}
            style={{
              background: isSelected ? col.hover : col.bg,
              border: `3px solid ${isSelected ? col.border : "transparent"}`,
              borderRadius: "1.25rem",
              padding: "16px 12px",
              cursor: disabled ? "not-allowed" : "pointer",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
              boxShadow: isSelected
                ? `0 6px 24px rgba(0,0,0,0.15), 0 0 0 4px ${col.border}44`
                : "0 2px 10px rgba(0,0,0,0.08)",
              transition: "border 0.15s, box-shadow 0.15s, background 0.15s",
              opacity: disabled && !isSelected ? 0.6 : 1,
            }}
          >
            <span style={{ fontSize: "2.8rem", lineHeight: 1 }}>{choice.emoji}</span>
            <span style={{
              fontSize: "1.1rem",
              fontWeight: 800,
              color: C.text,
              fontFamily: "'Nunito', sans-serif",
              textTransform: "capitalize",
            }}>
              {choice.word}
            </span>
          </motion.button>
        );
      })}
    </div>
  );
}

function getAgentColor(agentName: string) {
  const n = agentName.toLowerCase();
  if (n.includes("assessment")) return { bg: "oklch(0.96 0.03 230)", dot: C.sky, header: C.skyDark };
  if (n.includes("retrieval") || n.includes("rag")) return { bg: "oklch(0.96 0.04 145)", dot: C.green, header: C.greenDark };
  if (n.includes("lesson")) return { bg: "oklch(0.96 0.05 85)", dot: C.yellow, header: "oklch(0.60 0.15 85)" };
  if (n.includes("reinforcement")) return { bg: "oklch(0.96 0.04 350)", dot: C.pink, header: "oklch(0.62 0.14 350)" };
  return { bg: "oklch(0.96 0.04 280)", dot: C.coral, header: C.coralDark };
}

function LogCard({ log, index }: { log: ReasoningLog; index: number }) {
  const [open, setOpen] = useState(true);
  const colors = getAgentColor(log.agent);
  const steps = [
    { key: "THOUGHT" as const, label: "💭 Thought", color: C.skyDark },
    { key: "ACTION" as const, label: "⚡ Action", color: C.greenDark },
    { key: "OBSERVATION" as const, label: "👀 Observation", color: C.coralDark },
    { key: "PLAN" as const, label: "📋 Plan", color: "oklch(0.55 0.15 280)" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      style={{ borderRadius: 16, overflow: "hidden", border: `2px solid ${C.border}` }}
    >
      <div
        style={{ background: colors.bg, display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", cursor: "pointer", userSelect: "none" }}
        onClick={() => setOpen(!open)}
      >
        <span style={{ width: 11, height: 11, borderRadius: "50%", background: colors.dot, flexShrink: 0, display: "inline-block" }} />
        <span style={{ fontSize: "0.84rem", fontWeight: 800, flex: 1, color: colors.header }}>{log.agent}</span>
        <span style={{ fontSize: "0.72rem", opacity: 0.5, transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>▼</span>
      </div>
      {open && (
        <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8, background: C.card, borderTop: `2px solid ${C.border}` }}>
          {steps.filter(s => log[s.key]).map(s => (
            <div key={s.key}>
              <div style={{ fontSize: "0.7rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em", color: s.color, marginBottom: 2 }}>{s.label}</div>
              <div style={{ fontSize: "0.84rem", fontWeight: 600, color: C.text, lineHeight: 1.5, background: C.bg, borderRadius: 8, padding: "6px 10px" }}>{log[s.key]}</div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

const LETTER_EMOJIS: Record<string, string> = {
  A: "🍎", B: "🐻", C: "🐱", D: "🐕", E: "🐘", F: "🐸",
  G: "🐐", H: "🎩", I: "🍦", J: "🃏", K: "👑", L: "🦁",
  M: "🌙", N: "🪺", O: "🐙", P: "🐷", Q: "👸", R: "🐰",
  S: "☀️", T: "🐯", U: "☂️", V: "🌋", W: "🐋", X: "🦊",
  Y: "💛", Z: "🦓",
};

export default function App() {
  const [qState, setQState] = useState<QuestionState>({
    question: "Which of these words starts with the letter C?",
    current_letter: "C",
    choices: [],
  });
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnswerResponse | null>(null);
  const [pendingNext, setPendingNext] = useState<QuestionState | null>(null);
  const [speechText, setSpeechText] = useState(
    "Hello, Superstar! 🌟 I'm Ms. Sunny, and I'm here to help you learn to read!<br/><br/>Which word below starts with the letter shown? Tap a word card to answer!"
  );
  const autoAdvanceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingNextRef = useRef<QuestionState | null>(null);

  useEffect(() => {
    fetch("/question")
      .then(r => r.json())
      .then((data: QuestionState) => setQState(data))
      .catch(() => {});
    return () => {
      if (autoAdvanceTimer.current) clearTimeout(autoAdvanceTimer.current);
    };
  }, []);

  const advanceToNext = () => {
    if (autoAdvanceTimer.current) clearTimeout(autoAdvanceTimer.current);
    const next = pendingNextRef.current;
    if (next) {
      setQState(next);
      pendingNextRef.current = null;
      setPendingNext(null);
      setResult(null);
      setSelectedChoice(null);
    }
  };

  const submitChoice = async (word: string) => {
    if (loading) return;
    setSelectedChoice(word);
    setLoading(true);
    setResult(null);
    setPendingNext(null);

    try {
      const res = await fetch("/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: qState.question,
          answer: word,
          current_letter: qState.current_letter,
        }),
      });
      const data: AnswerResponse = await res.json();
      if (data.error) throw new Error(data.error);

      setResult(data);

      const nextState: QuestionState = {
        question: data.next_question,
        current_letter: data.current_letter,
        choices: data.choices || [],
      };

      pendingNextRef.current = nextState;
      setPendingNext(nextState);

      if (data.is_correct) {
        setSpeechText(`🌟 <strong>Amazing!</strong> "${word}" is right — great job!<br/><br/>You're moving to the next letter! Keep it up! 💪`);
        autoAdvanceTimer.current = setTimeout(advanceToNext, 5000);
      } else {
        const gaps = data.learning_gaps?.length
          ? `Let's work on: <em>${data.learning_gaps.join(", ")}</em>. `
          : "";
        setSpeechText(`💪 <strong>Good try!</strong> ${gaps}<br/>Read the explanation below and check the <strong>AI Thinking</strong> panel on the right — tap the button when you're ready! 🌈`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setSpeechText(`😅 Hmm, something went wrong.<br/>Error: ${msg}<br/>Make sure the backend is running!`);
    } finally {
      setLoading(false);
    }
  };

  const letter = qState.current_letter;
  const letterEmoji = letter ? (LETTER_EMOJIS[letter] ?? "🌟") : "🌟";

  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: "'Nunito', 'Arial Rounded MT Bold', sans-serif", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
        @keyframes spin-slow { to { transform: rotate(360deg); } }
        @keyframes pulse-dot { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.4);opacity:0.7} }
        @keyframes float { 0%,100%{transform:translateY(0) rotate(0deg)} 50%{transform:translateY(-12px) rotate(8deg)} }
        .bg-star { position:fixed; pointer-events:none; opacity:0.12; animation:float 6s ease-in-out infinite; }
        .thinking-panel::-webkit-scrollbar { width:5px; }
        .thinking-panel::-webkit-scrollbar-track { background:${C.bg}; border-radius:999px; }
        .thinking-panel::-webkit-scrollbar-thumb { background:${C.sky}; border-radius:999px; }
      `}</style>

      <div className="bg-star" style={{ top: "8%", left: "4%", fontSize: "2rem" }}>⭐</div>
      <div className="bg-star" style={{ top: "15%", right: "5%", fontSize: "1.4rem", animationDelay: "1s" }}>🌟</div>
      <div className="bg-star" style={{ top: "50%", left: "2%", fontSize: "1rem", animationDelay: "2s" }}>✨</div>
      <div className="bg-star" style={{ top: "72%", right: "4%", fontSize: "2.2rem", animationDelay: "0.5s" }}>⭐</div>
      <div className="bg-star" style={{ top: "88%", left: "12%", fontSize: "1.4rem", animationDelay: "1.5s" }}>🌟</div>

      <header style={{
        background: `linear-gradient(135deg, ${C.yellow} 0%, ${C.coral} 100%)`,
        borderRadius: "0 0 2rem 2rem",
        padding: "14px 28px",
        marginBottom: 24,
        boxShadow: "0 4px 24px rgba(0,0,0,0.15)",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span style={{ fontSize: "2.6rem", animation: "spin-slow 10s linear infinite", display: "inline-block" }}>☀️</span>
            <div>
              <h1 style={{ fontSize: "1.9rem", fontWeight: 900, color: "white", lineHeight: 1, textShadow: "0 2px 8px rgba(0,0,0,0.18)", margin: 0 }}>Ms. Sunny</h1>
              <p style={{ fontSize: "0.82rem", color: "rgba(255,255,255,0.88)", fontWeight: 700, margin: 0 }}>Your AI Reading Tutor</p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(255,255,255,0.22)", border: "2px solid rgba(255,255,255,0.45)", borderRadius: 999, padding: "6px 16px", fontSize: "0.78rem", fontWeight: 700, color: "white" }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#00ff88", boxShadow: "0 0 8px #00ff88", animation: "pulse-dot 2s infinite", display: "inline-block" }} />
            Powered by NVIDIA Nemotron
          </div>
        </div>
      </header>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 16px 40px", display: "grid", gridTemplateColumns: "1fr 370px", gap: 24, alignItems: "start" }}>

        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Avatar + Speech */}
          <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, flexShrink: 0 }}>
              <div style={{ width: 68, height: 68, background: `linear-gradient(135deg, ${C.yellow}, ${C.coral})`, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2.1rem", boxShadow: "0 4px 16px rgba(0,0,0,0.18)", border: "4px solid white" }}>☀️</div>
              <span style={{ fontSize: "0.72rem", fontWeight: 800, color: C.coral }}>Ms. Sunny</span>
            </div>
            <div style={{ background: C.card, borderRadius: "1.5rem", padding: "16px 20px", boxShadow: "0 6px 24px rgba(0,0,0,0.10)", flex: 1, border: `3px solid ${C.yellow}`, position: "relative" }}>
              <div style={{ position: "absolute", left: -15, top: 20, border: "7px solid transparent", borderRightColor: C.yellow }} />
              <div style={{ position: "absolute", left: -9, top: 22, border: "5px solid transparent", borderRightColor: C.card }} />
              <p style={{ fontSize: "0.97rem", lineHeight: 1.6, color: C.text, fontWeight: 600, margin: 0 }} dangerouslySetInnerHTML={{ __html: speechText }} />
            </div>
          </div>

          {/* Letter Card + Question */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
            <AnimatePresence mode="wait">
              {letter && (
                <motion.div key={letter} style={{ textAlign: "center" }}>
                  <LetterCard letter={letter} emoji={letterEmoji} />
                  <motion.p
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ marginTop: 12, fontSize: "0.82rem", fontWeight: 700, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em" }}
                  >
                    Letter {letter}
                  </motion.p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Question */}
          <div style={{ background: `linear-gradient(135deg, oklch(0.96 0.04 230), oklch(0.92 0.05 220))`, borderRadius: "1.75rem", padding: "20px 24px", border: `3px solid ${C.sky}`, boxShadow: "0 4px 16px rgba(0,0,0,0.08)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.82rem", fontWeight: 800, color: C.skyDark, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
              <span>❓</span> Question
            </div>
            <p style={{ fontSize: "1.2rem", fontWeight: 700, color: C.text, lineHeight: 1.5, margin: 0 }}>{qState.question}</p>
          </div>

          {/* Multiple Choice Grid */}
          <AnimatePresence mode="wait">
            {qState.choices.length > 0 ? (
              <motion.div key="choices" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
                <label style={{ fontSize: "0.95rem", fontWeight: 800, color: C.text, display: "block", marginBottom: 12 }}>
                  Tap the right word:
                </label>
                <MultipleChoice
                  choices={qState.choices}
                  onSelect={submitChoice}
                  disabled={loading || !!result}
                  selected={selectedChoice}
                />
              </motion.div>
            ) : (
              <motion.div key="loading-choices" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: "center", padding: "20px 0", color: C.muted, fontSize: "0.9rem", fontWeight: 600 }}>
                {loading ? "⏳ Thinking..." : "Loading word choices…"}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Result Card */}
          <AnimatePresence>
            {result && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                style={{
                  borderRadius: "1.75rem",
                  overflow: "hidden",
                  boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
                  border: `3px solid ${result.is_correct ? C.green : C.coral}`,
                }}
              >
                <div style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "14px 22px",
                  fontSize: "1.1rem", fontWeight: 800,
                  background: result.is_correct
                    ? `linear-gradient(135deg, ${C.green}, ${C.greenDark})`
                    : `linear-gradient(135deg, ${C.coral}, ${C.coralDark})`,
                  color: "white",
                }}>
                  <span style={{ fontSize: "1.5rem" }}>{result.is_correct ? "🌟" : "💪"}</span>
                  {result.is_correct ? "Awesome — you got it!" : "Good try! Let's learn!"}
                </div>
                <div style={{ padding: "16px 22px", background: C.card, display: "flex", flexDirection: "column", gap: 14 }}>
                  <div>
                    <h4 style={{ fontSize: "0.82rem", fontWeight: 800, color: C.muted, textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 8 }}>Ms. Sunny says:</h4>
                    <p style={{ fontSize: "0.97rem", fontWeight: 600, lineHeight: 1.6, color: C.text, margin: 0 }}>{result.explanation}</p>
                  </div>

                  {!result.is_correct && (
                    <div style={{
                      display: "flex", alignItems: "center", gap: 10,
                      background: "oklch(0.96 0.04 230)",
                      border: `2px solid ${C.sky}`,
                      borderRadius: "1rem",
                      padding: "10px 14px",
                      fontSize: "0.86rem", fontWeight: 700, color: C.skyDark,
                    }}>
                      <span style={{ fontSize: "1.2rem", flexShrink: 0 }}>🤖</span>
                      <span>Check the <strong>AI Thinking</strong> panel on the right to see how the agents figured it out!</span>
                    </div>
                  )}

                  {pendingNext && (
                    <motion.button
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={advanceToNext}
                      style={{
                        background: result.is_correct
                          ? `linear-gradient(135deg, ${C.green}, ${C.greenDark})`
                          : `linear-gradient(135deg, ${C.coral}, ${C.coralDark})`,
                        color: "white",
                        border: "none",
                        borderRadius: "999px",
                        padding: "14px 28px",
                        fontFamily: "'Nunito', sans-serif",
                        fontSize: "1.05rem",
                        fontWeight: 800,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 10,
                        boxShadow: "0 4px 16px rgba(0,0,0,0.18)",
                        width: "100%",
                      }}
                    >
                      {result.is_correct ? (
                        <><span>🚀</span> Keep going — next letter!</>
                      ) : (
                        <><span>💡</span> I understand — try next question!</>
                      )}
                    </motion.button>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* AI Thinking Panel */}
        <aside
          className="thinking-panel"
          style={{ background: C.card, borderRadius: "1.75rem", padding: 20, boxShadow: "0 8px 32px rgba(0,0,0,0.10)", border: `3px solid ${C.border}`, display: "flex", flexDirection: "column", gap: 14, position: "sticky", top: 20, maxHeight: "90vh", overflowY: "auto" }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <span style={{ fontSize: "1.5rem" }}>🤖</span>
            <h2 style={{ fontSize: "1.15rem", fontWeight: 900, color: C.coral, flex: 1, margin: 0 }}>AI Thinking</h2>
            <span style={{ fontSize: "0.68rem", fontWeight: 800, background: `linear-gradient(135deg, ${C.coral}, ${C.pink})`, color: "white", padding: "4px 11px", borderRadius: 999, textTransform: "uppercase", letterSpacing: "0.05em" }}>Multi-Agent</span>
          </div>

          <div style={{ fontSize: "0.86rem", color: C.muted, fontWeight: 600, lineHeight: 1.5, padding: "10px 14px", background: C.bg, borderRadius: "1rem" }}>
            Watch how Ms. Sunny's 4 AI agents reason step by step to help you learn!
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {[
              { label: "Assessment Agent", color: C.sky },
              { label: "Retrieval Agent (RAG)", color: C.green },
              { label: "Lesson Generator", color: C.yellow },
              { label: "Reinforcement Agent", color: C.pink },
            ].map(item => (
              <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.8rem", fontWeight: 700, color: C.muted }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: item.color, flexShrink: 0, display: "inline-block", border: item.color === C.yellow ? "1.5px solid #ccc" : "none" }} />
                {item.label}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {loading && (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, padding: 16, fontSize: "0.88rem", fontWeight: 700, color: C.coral }}>
                <div style={{ width: 20, height: 20, border: `3px solid ${C.border}`, borderTopColor: C.coral, borderRadius: "50%", animation: "spin-slow 0.8s linear infinite" }} />
                Agents are thinking…
              </div>
            )}
            {!loading && result && result.reasoning_logs?.length > 0 ? (
              result.reasoning_logs.map((log, i) => <LogCard key={i} log={log} index={i} />)
            ) : !loading && (
              <div style={{ textAlign: "center", padding: "20px 14px" }}>
                <div style={{ fontSize: "2.2rem", marginBottom: 10 }}>💭</div>
                <p style={{ fontSize: "0.86rem", color: C.border, fontWeight: 600, lineHeight: 1.5, margin: 0 }}>
                  Tap a word card to see the AI agents thinking in action!
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
