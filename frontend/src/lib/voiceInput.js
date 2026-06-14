/**
 * Voice Input module wrapping the Web Speech API.
 * Provides a simple interface to start/stop speech recognition
 * for journal entry dictation.
 */

let recognition = null;
let silenceTimer = null;
let pauseTimer = null;

const PAUSE_TIMEOUT_MS = 3000; // 3-second pause auto-stops
const SILENCE_TIMEOUT_MS = 10000; // 10-second silence timeout

export const voiceInput = {
    /**
     * Check if the Web Speech API is supported in the current browser.
     * @returns {boolean}
     */
    isSupported() {
        return !!(
            window.SpeechRecognition || window.webkitSpeechRecognition
        );
    },

    /**
     * Start speech recognition.
     * @param {(transcript: string) => void} onTranscript - Called with interim/final transcript text
     * @param {(message: string) => void} onError - Called with a user-friendly error message
     * @param {() => void} onEnd - Called when recording ends (manual stop or timeout)
     */
    start(onTranscript, onError, onEnd) {
        if (!this.isSupported()) {
            onError("Voice input is not supported in this browser.");
            return;
        }

        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        let finalTranscript = "";
        let hasReceivedSpeech = false;

        // Start the 10-second silence timeout
        silenceTimer = setTimeout(() => {
            if (!hasReceivedSpeech) {
                this.stop();
                onError("No speech detected. Try again in a quieter environment.");
            }
        }, SILENCE_TIMEOUT_MS);

        recognition.onresult = (event) => {
            hasReceivedSpeech = true;

            // Clear silence timer once speech is detected
            if (silenceTimer) {
                clearTimeout(silenceTimer);
                silenceTimer = null;
            }

            // Reset the 3-second pause timer on each result
            if (pauseTimer) {
                clearTimeout(pauseTimer);
            }

            let interimTranscript = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                if (result.isFinal) {
                    finalTranscript += result[0].transcript;
                } else {
                    interimTranscript += result[0].transcript;
                }
            }

            // Send current transcript (final + interim) for real-time display
            onTranscript(finalTranscript + interimTranscript);

            // Start 3-second pause timer to auto-stop
            pauseTimer = setTimeout(() => {
                this.stop();
            }, PAUSE_TIMEOUT_MS);
        };

        recognition.onerror = (event) => {
            this._cleanup();

            if (event.error === "not-allowed") {
                onError("Microphone access is required for voice input.");
            } else if (event.error === "no-speech") {
                onError("No speech detected. Try again in a quieter environment.");
            } else {
                onError("Voice input error. Please try again.");
            }
            onEnd();
        };

        recognition.onend = () => {
            this._cleanup();
            // Send final transcript one last time
            if (finalTranscript) {
                onTranscript(finalTranscript);
            }
            onEnd();
        };

        try {
            recognition.start();
        } catch (err) {
            this._cleanup();
            onError("Could not start voice input. Please try again.");
            onEnd();
        }
    },

    /**
     * Stop speech recognition manually.
     */
    stop() {
        if (recognition) {
            try {
                recognition.stop();
            } catch {
                // Already stopped
            }
        }
        this._cleanup();
    },

    /**
     * Clean up timers.
     * @private
     */
    _cleanup() {
        if (silenceTimer) {
            clearTimeout(silenceTimer);
            silenceTimer = null;
        }
        if (pauseTimer) {
            clearTimeout(pauseTimer);
            pauseTimer = null;
        }
    },
};
