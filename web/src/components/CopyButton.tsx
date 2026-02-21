import { useState } from 'react'

type CopyButtonProps = { text: string }

export default function CopyButton({ text }: CopyButtonProps) {
    const [copied, setCopied] = useState(false)

    const copy = async () => {
        await navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={copy}>
            {copied ? '✓ Copied' : '⎘ Copy'}
        </button>
    )
}
