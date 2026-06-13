import React, { useState, useRef } from "react";
import { motion } from "framer-motion";

export const InviteCodeInput = ({ onSubmit, loading = false, error = "" }) => {
    const [code, setCode] = useState(["", "", "", "", "", ""]);
    const inputsRef = useRef([]);

    const handleChange = (index, value) => {
        // Only allow alphanumeric
        const cleaned = value.replace(/[^a-zA-Z0-9]/g, "").slice(0, 1).toUpperCase();
        const newCode = [...code];
        newCode[index] = cleaned;
        setCode(newCode);

        // Auto-focus next input
        if (cleaned && index < 5) {
            inputsRef.current[index + 1]?.focus();
        }
    };

    const handleKeyDown = (index, e) => {
        if (e.key === "Backspace" && !code[index] && index > 0) {
            inputsRef.current[index - 1]?.focus();
        }
    };

    const handlePaste = (e) => {
        e.preventDefault();
        const pasted = e.clipboardData
            .getData("text")
            .replace(/[^a-zA-Z0-9]/g, "")
            .toUpperCase()
            .slice(0, 6);
        const newCode = [...code];
        for (let i = 0; i < 6; i++) {
            newCode[i] = pasted[i] || "";
        }
        setCode(newCode);
        // Focus last filled or the next empty
        const lastIdx = Math.min(pasted.length, 5);
        inputsRef.current[lastIdx]?.focus();
    };

    const fullCode = code.join("");
    const isValid = fullCode.length === 6;

    const handleSubmit = () => {
        if (isValid && onSubmit) {
            onSubmit(fullCode);
        }
    };

    return (
        <div data-testid="invite-code-input" className="flex flex-col items-center gap-4">
            <div className="flex gap-2" onPaste={handlePaste}>
                {code.map((char, i) => (
                    <input
                        key={i}
                        ref={(el) => (inputsRef.current[i] = el)}
                        data-testid={`invite-char-${i}`}
                        type="text"
                        inputMode="text"
                        maxLength={1}
                        value={char}
                        onChange={(e) => handleChange(i, e.target.value)}
                        onKeyDown={(e) => handleKeyDown(i, e)}
                        className="w-10 h-12 text-center text-lg font-bold rounded-xl border-2 border-slate-200 focus:border-purple-400 focus:ring-2 focus:ring-purple-100 outline-none transition-all bg-white"
                    />
                ))}
            </div>

            {error && (
                <p data-testid="invite-error" className="text-xs text-red-500 font-medium">
                    {error}
                </p>
            )}

            <motion.button
                data-testid="invite-submit"
                whileTap={{ scale: 0.95 }}
                onClick={handleSubmit}
                disabled={!isValid || loading}
                className="w-full py-2.5 rounded-full text-sm font-semibold text-white bdy-bg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
                {loading ? "Joining…" : "Join Group"}
            </motion.button>
        </div>
    );
};

export default InviteCodeInput;
