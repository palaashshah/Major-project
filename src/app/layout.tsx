import type { Metadata } from "next"
import { Space_Grotesk, DM_Sans, Fira_Code } from "next/font/google"
import "./globals.css"  

export const metadata: Metadata = {
    title: "OpenGlass Portfolio",
}

const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-heading" })
const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-body" })
const firaCode = Fira_Code({ subsets: ["latin"], variable: "--font-mono" })

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className={`${spaceGrotesk.variable} ${dmSans.variable} ${firaCode.variable}`}>
            <body>{children}</body>
        </html>
    )
}