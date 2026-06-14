import React, { useState, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { REGISTER } from "../constants/testIds/auth";
import { Loader2, Mail, Lock, Check, X } from "lucide-react";

const PASSWORD_REQUIREMENTS = [
    { label: "At least 8 characters", test: (p) => p.length >= 8 },
    { label: "One uppercase letter", test: (p) => /[A-Z]/.test(p) },
    { label: "One number", test: (p) => /\d/.test(p) },
];

const RegisterPage = () => {
    const { register } = useAuth();
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const requirementStatus = useMemo(
        () => PASSWORD_REQUIREMENTS.map((req) => ({ ...req, met: req.test(password) })),
        [password]
    );

    const allRequirementsMet = requirementStatus.every((r) => r.met);

    const validate = () => {
        if (!email.trim()) return "Email is required";
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Please enter a valid email";
        if (!allRequirementsMet) return "Password does not meet all requirements";
        if (password !== confirmPassword) return "Passwords do not match";
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
            await register(email, password);
            navigate("/", { replace: true });
        } catch (err) {
            const message =
                err?.response?.data?.detail ||
                err?.response?.data?.message ||
                "An account with this email already exists";
            setError(message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-full px-4 py-8">
            <div className="w-full max-w-sm">
                <div className="text-center mb-6">
                    <h1 className="text-2xl font-bold font-[Outfit] text-slate-900">Create account</h1>
                    <p className="text-sm text-slate-500 mt-1 font-[Plus_Jakarta_Sans]">
                        Get started with PocketBuddy
                    </p>
                </div>

                <Card className="rounded-2xl shadow-sm border border-slate-100">
                    <CardContent className="p-6">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {error && (
                                <div
                                    className="bg-red-50 text-red-600 text-sm rounded-lg px-3 py-2 border border-red-100"
                                    role="alert"
                                    data-testid="register-error"
                                >
                                    {error}
                                </div>
                            )}

                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="pl-9"
                                        data-testid={REGISTER.emailInput}
                                        autoComplete="email"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="password">Password</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                    <Input
                                        id="password"
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="pl-9"
                                        data-testid={REGISTER.passwordInput}
                                        autoComplete="new-password"
                                    />
                                </div>

                                {/* Password requirements display */}
                                <div className="space-y-1 pt-1">
                                    {requirementStatus.map((req, idx) => (
                                        <div
                                            key={idx}
                                            className={`flex items-center gap-2 text-xs ${req.met ? "text-green-600" : "text-slate-400"
                                                }`}
                                        >
                                            {req.met ? (
                                                <Check className="h-3 w-3" />
                                            ) : (
                                                <X className="h-3 w-3" />
                                            )}
                                            <span>{req.label}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="confirmPassword">Confirm Password</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                    <Input
                                        id="confirmPassword"
                                        type="password"
                                        placeholder="••••••••"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="pl-9"
                                        data-testid={REGISTER.passwordConfirmInput}
                                        autoComplete="new-password"
                                    />
                                </div>
                            </div>

                            <Button
                                type="submit"
                                className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded-xl"
                                disabled={isSubmitting}
                                data-testid={REGISTER.submitButton}
                                aria-label="Create your account"
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Creating account...
                                    </>
                                ) : (
                                    "Create account"
                                )}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <p className="text-center text-sm text-slate-500 mt-4">
                    Already have an account?{" "}
                    <Link
                        to="/login"
                        className="text-purple-600 hover:text-purple-700 font-medium"
                        data-testid={REGISTER.loginLink}
                    >
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
};

export default RegisterPage;
