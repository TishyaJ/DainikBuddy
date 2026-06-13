import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Loader2, Mail, ArrowLeft, CheckCircle2 } from "lucide-react";

const ForgotPasswordPage = () => {
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const validate = () => {
        if (!email.trim()) return "Email is required";
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Please enter a valid email";
        return null;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

        const validationError = validate();
        if (validationError) {
            setError(validationError);
            return;
        }

        setIsSubmitting(true);
        try {
            await api.post("/auth/forgot-password", { email });
            setIsSuccess(true);
        } catch (err) {
            // Always show success message to avoid email enumeration
            setIsSuccess(true);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-full px-4 py-8">
            <div className="w-full max-w-sm">
                <div className="text-center mb-6">
                    <h1 className="text-2xl font-bold font-[Outfit] text-slate-900">Reset password</h1>
                    <p className="text-sm text-slate-500 mt-1 font-[Plus_Jakarta_Sans]">
                        We'll send you a link to reset your password
                    </p>
                </div>

                <Card className="rounded-2xl shadow-sm border border-slate-100">
                    <CardContent className="p-6">
                        {isSuccess ? (
                            <div className="text-center py-4 space-y-3" data-testid="forgot-password-success">
                                <CheckCircle2 className="h-10 w-10 text-green-500 mx-auto" />
                                <p className="text-sm text-slate-600">
                                    If an account with that email exists, a password reset link has been sent.
                                </p>
                                <p className="text-xs text-slate-400">Check your email inbox and spam folder.</p>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-4">
                                {error && (
                                    <div
                                        className="bg-red-50 text-red-600 text-sm rounded-lg px-3 py-2 border border-red-100"
                                        role="alert"
                                        data-testid="forgot-password-error"
                                    >
                                        {error}
                                    </div>
                                )}

                                <div className="space-y-2">
                                    <Label htmlFor="email">Email address</Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                        <Input
                                            id="email"
                                            type="email"
                                            placeholder="you@example.com"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="pl-9"
                                            data-testid="forgot-password-email-input"
                                            autoComplete="email"
                                        />
                                    </div>
                                </div>

                                <Button
                                    type="submit"
                                    className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded-xl"
                                    disabled={isSubmitting}
                                    data-testid="forgot-password-submit-button"
                                >
                                    {isSubmitting ? (
                                        <>
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            Sending...
                                        </>
                                    ) : (
                                        "Send reset link"
                                    )}
                                </Button>
                            </form>
                        )}
                    </CardContent>
                </Card>

                <div className="text-center mt-4">
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 font-medium"
                        data-testid="forgot-password-login-link"
                    >
                        <ArrowLeft className="h-3 w-3" />
                        Back to sign in
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default ForgotPasswordPage;
