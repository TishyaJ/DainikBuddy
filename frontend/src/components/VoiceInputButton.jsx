import React, { useState, useCallback } from "react";
import { Mic, MicOff } from "lucide-react";
import { motion } from "framer-motion";
import { voiceInput } from "../lib/voiceInput";

/**
 * VoiceInputButton - A mic button that toggles speech recognition.
 * Shows a pulsing animation when recording.
 * Hides itself if Web Speech API is not supported.
 *
 * @param {Object} props
 * @param {(text: string) => void} props.onTranscript - Called with transcript text during/after recording
 * @param {(message: string) => void} props.onError - Called with user-friendly error message
 * @param {() => void} props.onEnd - Called when recording ends
 * @param {() => void} [props.onStart] - Called when recording starts
 * @param {boolean} [props.disabled] - Whether the button is disabled
 * @param {string} [props.className] - Additional CSS classes
 */
export function VoiceInputButton({ onTranscript, onError, onEnd, onStart, disabled, className = "" }) {
    const [isRecording, setIsRecording] = useState(false);

    const handleToggle = useCallback(() => {
        if (isRecording) {
            voiceInput.stop();
            setIsRecording(false);
        } else {
            setIsRecording(true);
            if (onStart) onStart();
            voiceInput.start(
                (transcript) => {
                    onTranscript(transcript);
                },
                (message) => {
                    setIsRecording(false);
                    onError(message);
                },
                () => {
                    setIsRecording(false);
                    if (onEnd) onEnd();
                }
            );
        }
    }, [isRecording, onTranscript, onError, onEnd, onStart]);

    // Hide button entirely if Web Speech API is not supported
    if (!voiceInput.isSupported()) {
        return null;
    }

    return (
        <button
            data-testid="voice-journal-btn"
            onClick={handleToggle}
            disabled={disabled}
            className={`relative font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 transition-all active:scale-95 ${isRecording
                    ? "bg-red-50 border border-red-400 text-red-600"
                    : "bg-white border border-[color:var(--bdy)] text-[color:var(--bdy)]"
                } ${disabled ? "opacity-50 cursor-not-allowed" : ""} ${className}`}
            aria-label={isRecording ? "Stop recording" : "Start voice input"}
        >
            {/* Pulsing ring animation when recording */}
            {isRecording && (
                <motion.span
                    className="absolute inset-0 rounded-xl border-2 border-red-400"
                    animate={{ scale: [1, 1.05, 1], opacity: [1, 0.5, 1] }}
                    transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                />
            )}

            {isRecording ? (
                <>
                    <motion.span
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 0.8, repeat: Infinity }}
                    >
                        <MicOff className="w-4 h-4" />
                    </motion.span>
                    <span className="text-sm">Stop</span>
                </>
            ) : (
                <>
                    <Mic className="w-4 h-4" />
                    <span className="text-sm">Voice</span>
                </>
            )}
        </button>
    );
}
