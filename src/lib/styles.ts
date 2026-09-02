// styles.ts — shared style objects used across components
// instead of repeating the same styles in every file, we define them once here and import them
// this is the CSS-in-JS equivalent of a shared stylesheet
// defined once here, imported everywhere — avoids repetition

// input on DARK background (charcoal) — text must be ivory
export const inputStyle = {
    width: "100%",
    padding: "12px 16px",
    backgroundColor: "rgba(255,255,255,0.07)",  // subtle light tint on dark bg
    border: "1px solid var(--silver)",
    borderRadius: "8px",
    fontFamily: "var(--font-body)",
    fontSize: "14px",
    color: "var(--ivory)",                       // ivory text — readable on charcoal
    outline: "none"
}

// input on IVORY background — text must be charcoal
export const inputStyleLight = {
    width: "100%",
    padding: "12px 16px",
    backgroundColor: "rgba(0,0,0,0.04)",
    border: "1px solid var(--silver)",
    borderRadius: "8px",
    fontFamily: "var(--font-body)",
    fontSize: "14px",
    color: "var(--charcoal)",                    // charcoal text — readable on ivory
    outline: "none"
}

// label on DARK background
export const labelStyle = {
    fontFamily: "var(--font-body)",
    fontSize: "11px",
    color: "var(--silver)",                      // silver — subtle on charcoal
    textTransform: "uppercase" as const,
    letterSpacing: "0.1em",
    marginBottom: "6px",
    display: "block"
}

// label on IVORY background
export const labelStyleLight = {
    fontFamily: "var(--font-body)",
    fontSize: "11px",
    color: "var(--slate)",                       // slate — subtle on ivory
    textTransform: "uppercase" as const,
    letterSpacing: "0.1em",
    marginBottom: "6px",
    display: "block"
}

// button factory — returns style based on disabled state
// usage: buttonStyle(false) = active | buttonStyle(true) = greyed out
export const buttonStyle = (disabled: boolean) => ({
    padding: "13px 28px",
    borderRadius: "8px",
    backgroundColor: disabled ? "rgba(255,255,255,0.1)" : "var(--ivory)",
    color: disabled ? "rgba(255,255,255,0.3)" : "var(--charcoal)",
    fontFamily: "var(--font-heading)",
    fontSize: "14px",
    fontWeight: 600,
    border: "none",
    cursor: disabled ? "not-allowed" : "pointer",
    transition: "all 0.2s ease"
})

// dark button for ivory backgrounds (used in questionnaire)
export const buttonStyleDark = (disabled: boolean) => ({
    padding: "13px 28px",
    borderRadius: "8px",
    backgroundColor: disabled ? "var(--silver)" : "var(--charcoal)",
    color: disabled ? "var(--charcoal)" : "var(--ivory)",
    fontFamily: "var(--font-heading)",
    fontSize: "14px",
    fontWeight: 600,
    border: "none",
    cursor: disabled ? "not-allowed" : "pointer",
    transition: "all 0.2s ease"
})

export const backButtonStyle = {
    background: "none",
    border: "none",
    fontFamily: "var(--font-body)" as const,
    fontSize: "13px",
    color: "rgba(255,255,255,0.5)",              // semi-transparent white on dark bg
    cursor: "pointer"
}

export const backButtonStyleLight = {
    background: "none",
    border: "none",
    fontFamily: "var(--font-body)" as const,
    fontSize: "13px",
    color: "var(--slate)",                       // slate on ivory bg
    cursor: "pointer"
}