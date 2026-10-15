'use client';

import { useState } from 'react';
import { LogIn, UserPlus, Mail, Lock, User, Loader2 } from 'lucide-react';
import { apiFetch } from '../api';

interface LoginSignupProps {
    onAuthSuccess: (user: any) => void;
}

export default function LoginSignup({ onAuthSuccess }: LoginSignupProps) {
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const endpoint = isLogin ? '/api/auth/login/' : '/api/auth/signup/';

        try {
            const res = await apiFetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || 'Something went wrong');
            }

            onAuthSuccess(data.user);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4 font-sans">
            <div className="w-full max-w-md bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden animate-in fade-in zoom-in duration-500">
                <div className="p-8">
                    <div className="flex justify-center mb-8">
                        <div className="w-16 h-16 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-600/20 ring-4 ring-indigo-500/10">
                            {isLogin ? <LogIn size={32} /> : <UserPlus size={32} />}
                        </div>
                    </div>

                    <h2 className="text-3xl font-bold text-center text-zinc-900 dark:text-zinc-100 mb-2 tracking-tight">
                        {isLogin ? 'Welcome Back' : 'Create Account'}
                    </h2>
                    <p className="text-center text-zinc-500 dark:text-zinc-400 text-sm mb-8">
                        {isLogin ? 'Sign in to access your loan assistant' : 'Sign up to get started with your loan assistant'}
                    </p>

                    {error && (
                        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 rounded-xl text-red-600 dark:text-red-400 text-sm animate-shake">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {!isLogin && (
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-400">
                                    <User size={18} />
                                </div>
                                <input
                                    type="text"
                                    required
                                    placeholder="Full Name"
                                    className="w-full pl-11 pr-4 py-3.5 bg-zinc-50 dark:bg-zinc-800 border-none rounded-xl focus:ring-2 focus:ring-indigo-500/20 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 text-sm transition-all"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>
                        )}

                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-400">
                                <Mail size={18} />
                            </div>
                            <input
                                type="email"
                                required
                                placeholder="Email Address"
                                className="w-full pl-11 pr-4 py-3.5 bg-zinc-50 dark:bg-zinc-800 border-none rounded-xl focus:ring-2 focus:ring-indigo-500/20 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 text-sm transition-all"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            />
                        </div>

                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-400">
                                <Lock size={18} />
                            </div>
                            <input
                                type="password"
                                required
                                placeholder="Password"
                                className="w-full pl-11 pr-4 py-3.5 bg-zinc-50 dark:bg-zinc-800 border-none rounded-xl focus:ring-2 focus:ring-indigo-500/20 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 text-sm transition-all"
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-4 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-500/20 transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {loading ? <Loader2 className="animate-spin" size={20} /> : (isLogin ? 'Sign In' : 'Sign Up')}
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-zinc-100 dark:border-zinc-800 text-center">
                        <button
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-sm font-medium text-zinc-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                        >
                            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
