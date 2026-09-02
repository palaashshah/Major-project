"use client"
import { useState } from "react"
import { questions } from "@/lib/questions"
import { buttonStyleDark, backButtonStyleLight } from "@/lib/styles"

// sidebar labels for each question
const questionLabels = [
    "Investment horizon", "Primary goal", "Market reaction",
    "Fear factor", "Risk vs reward", "Market knowledge",
    "Acceptable loss", "Return expectations", "Investment approach"
]

type Props = {
    onComplete: (profile: string, horizon: string) => void
}

export default function RiskQuestionnaire({ onComplete }: Props) {
    const [currentQuestion, setCurrentQuestion] = useState(0)
    const [totalScore, setTotalScore] = useState(0)
    const [horizon, setHorizon] = useState("")
    const [selected, setSelected] = useState<number | null>(null)  // index of selected option

    function handleAnswer(points: number) {
        const newScore = totalScore + points

        // local variable — available immediately, avoids async state issue
        let newHorizon = horizon

        // Q4 (index 0) maps directly to investment_horizon
        if (currentQuestion === 0) {
            if (points === 3) newHorizon = "short"
            else if (points === 6) newHorizon = "medium"
            else if (points === 9) newHorizon = "long"
            else newHorizon = "very_long"
            setHorizon(newHorizon)
        }

        if (currentQuestion === questions.length - 1) {
            // last question — send results up to parent
            onComplete(getRiskProfile(newScore), newHorizon)
        } else {
            setCurrentQuestion(currentQuestion + 1)
            setSelected(null)  // reset selection for next question
        }
        setTotalScore(newScore)
    }

    function getRiskProfile(score: number): string {
        if (score <= 20) return "guardian"
        else if (score <= 40) return "defender"
        else if (score <= 60) return "moderator"
        else if (score <= 80) return "builder"
        else return "explorer"
    }

    // full screen split — left sidebar + right content
    return (
        <div style={{
            display: "flex", height: "100vh", width: "100vw",
            backgroundColor: "var(--charcoal)"
        }}>
            {/* ── LEFT SIDEBAR ── */}
            <div style={{
                width: "280px", flexShrink: 0,
                backgroundColor: "var(--charcoal)",
                borderRight: "1px solid rgba(255,255,255,0.1)",
                padding: "48px 24px",
                display: "flex", flexDirection: "column", gap: "4px"
            }}>
                {/* logo / title */}
                <p style={{
                    fontFamily: "var(--font-heading)", fontSize: "11px",
                    fontWeight: 700, letterSpacing: "0.15em",
                    textTransform: "uppercase", color: "rgba(255,255,255,0.4)",
                    marginBottom: "32px"
                }}>Risk Assessment</p>

                {/* question list */}
                {questionLabels.map((label, index) => {
                    const isDone = index < currentQuestion      // already answered
                    const isCurrent = index === currentQuestion // currently on this one
                    return (
                        <div key={label} style={{
                            display: "flex", alignItems: "center", gap: "12px",
                            padding: "10px 12px", borderRadius: "8px",
                            backgroundColor: isCurrent ? "rgba(255,255,255,0.08)" : "transparent",
                            opacity: index > currentQuestion ? 0.35 : 1,
                            transition: "all 0.2s ease"
                        }}>
                            {/* circle indicator */}
                            <div style={{
                                width: "26px", height: "26px", borderRadius: "50%", flexShrink: 0,
                                backgroundColor: isDone ? "var(--slate)" : isCurrent ? "rgba(255,255,255,0.15)" : "transparent",
                                border: `1.5px solid ${isDone ? "var(--slate)" : isCurrent ? "rgba(255,255,255,0.4)" : "rgba(255,255,255,0.2)"}`,
                                display: "flex", alignItems: "center", justifyContent: "center"
                            }}>
                                {isDone
                                    ? <span style={{ color: "var(--ivory)", fontSize: "11px" }}>✓</span>
                                    : <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "rgba(255,255,255,0.6)" }}>{index + 1}</span>
                                }
                            </div>
                            <span style={{
                                fontFamily: "var(--font-body)", fontSize: "13px",
                                color: isCurrent ? "var(--ivory)" : "rgba(255,255,255,0.6)",
                                fontWeight: isCurrent ? 600 : 400
                            }}>{label}</span>
                        </div>
                    )
                })}
            </div>

            {/* ── RIGHT CONTENT ── */}
            <div style={{
                flex: 1, backgroundColor: "var(--ivory)",
                padding: "56px 64px",
                display: "flex", flexDirection: "column", justifyContent: "space-between"
            }}>
                <div>
                    {/* step label */}
                    <p style={{
                        fontFamily: "var(--font-mono)", fontSize: "11px",
                        color: "var(--slate)", letterSpacing: "0.12em",
                        textTransform: "uppercase", marginBottom: "20px"
                    }}>
                        Risk Profile · Step {currentQuestion + 1}
                    </p>

                    {/* question */}
                    <h2 style={{
                        fontFamily: "var(--font-heading)", fontSize: "28px",
                        color: "var(--charcoal)", fontWeight: 700,
                        lineHeight: 1.3, marginBottom: "40px", maxWidth: "560px"
                    }}>
                        {questions[currentQuestion].question}
                    </h2>

                    {/* options — clicking selects, Continue button submits */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "12px", maxWidth: "600px" }}>
                        {questions[currentQuestion].options.map((option, i) => (
                            <div
                                key={option.label}
                                onClick={() => setSelected(i)}  // just selects, doesn't submit
                                style={{
                                    display: "flex", alignItems: "center", gap: "16px",
                                    padding: "16px 20px", borderRadius: "10px", cursor: "pointer",
                                    border: `1.5px solid ${selected === i ? "var(--slate)" : "var(--silver)"}`,
                                    backgroundColor: selected === i ? "rgba(109,129,150,0.12)" : "transparent",
                                    transition: "all 0.15s ease"
                                }}
                            >
                                {/* radio circle */}
                                <div style={{
                                    width: "18px", height: "18px", borderRadius: "50%", flexShrink: 0,
                                    border: `2px solid ${selected === i ? "var(--slate)" : "var(--silver)"}`,
                                    backgroundColor: selected === i ? "var(--slate)" : "transparent",
                                    transition: "all 0.15s ease"
                                }} />
                                <span style={{
                                    fontFamily: "var(--font-body)", fontSize: "15px",
                                    color: "var(--charcoal)", lineHeight: 1.4
                                }}>
                                    {option.label}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* bottom bar — back + continue */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "40px" }}>
                    <button
                        onClick={() => {
                            if (currentQuestion > 0) {
                                setCurrentQuestion(currentQuestion - 1)
                                setSelected(null)
                            }
                        }}
                        style={{ ...backButtonStyleLight, opacity: currentQuestion === 0 ? 0 : 1 }}
                    >
                        ← Back
                    </button>

                    {/* continue only active when something is selected */}
                    <button
                        onClick={() => { if (selected !== null) handleAnswer(questions[currentQuestion].options[selected].points) }}
                        disabled={selected === null}
                        style={buttonStyleDark(selected === null)}
                    >
                        Continue
                    </button>
                </div>
            </div>
        </div>
    )
}
