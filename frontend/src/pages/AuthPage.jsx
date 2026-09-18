import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { HeartPulse, LockKeyhole, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AuthPage({ mode }) {
    const isRegister = mode === 'register';

    const [form, setForm] = useState({
        role: 'patient',
    });

    const [error, setError] = useState('');

    const { login, register } = useAuth();
    const navigate = useNavigate();

    const submit = async (event) => {
        event.preventDefault();
        setError('');

        try {
            const user = isRegister
                ? await register(form)
                : await login(form);

            navigate(user.role === 'relative' ? '/relative' : '/');
        } catch (err) {
            setError(
                err.response?.data?.message ||
                'Unable to connect to the care service.'
            );
        }
    };

    const change = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value,
        });
    };

    return (
        <div className="auth-page">
            <div className="auth-art">
                <div className="brand light">
                    <span className="brand-mark">
                        <HeartPulse size={19} />
                    </span>
                    med<span>mate</span>
                </div>

                <div className="art-copy">
                    <span className="eyebrow">
                        A calmer way to remember
                    </span>

                    <h1>
                        Small reminders.
                        <br />
                        <em>More good days.</em>
                    </h1>

                    <p>
                        Keep medicine routines visible, understandable, and shared
                        with the people who care.
                    </p>
                </div>

                <div className="art-foot">
                    Private by design · Built for everyday care
                </div>
            </div>

            <div className="auth-form-wrap">
                <form
                    className="auth-form"
                    onSubmit={submit}
                >
                    <span className="eyebrow">
                        {isRegister
                            ? 'JOIN YOUR CARE CIRCLE'
                            : 'WELCOME BACK'}
                    </span>

                    <h2>
                        {isRegister
                            ? 'Create your account'
                            : 'Sign in to medmate'}
                    </h2>

                    <p className="muted">
                        {isRegister
                            ? 'Start a routine that works for you.'
                            : 'Your daily rhythm is waiting.'}
                    </p>

                    {isRegister && (
                        <label>
                            Full name
                            <input
                                name="full_name"
                                required
                                onChange={change}
                                placeholder="Enter your name"
                            />
                        </label>
                    )}

                    <label>
                        Email
                        <input
                            name="email"
                            type="email"
                            required
                            onChange={change}
                            placeholder="you@example.com"
                        />
                    </label>

                    {isRegister && (
                        <label>
                            Phone
                            <input
                                name="phone"
                                onChange={change}
                                placeholder="+91 98765 43210"
                            />
                        </label>
                    )}

                    <label>
                        Password

                        <div className="input-icon">
                            <LockKeyhole size={16} />

                            <input
                                name="password"
                                type="password"
                                required
                                onChange={change}
                                placeholder="At least 8 characters"
                            />
                        </div>
                    </label>

                    {isRegister && (
                        <label>
                            Account type

                            <select
                                name="role"
                                value={form.role}
                                onChange={change}
                            >
                                <option value="patient">
                                    Patient
                                </option>

                                <option value="relative">
                                    Relative / caregiver
                                </option>
                            </select>
                        </label>
                    )}

                    {error && (
                        <div className="error-box">
                            {error}
                        </div>
                    )}

                    <button
                        className="primary wide"
                        type="submit"
                    >
                        {isRegister
                            ? 'Create account'
                            : 'Sign in'}{' '}
                        <span>→</span>
                    </button>

                    <p className="switch">
                        {isRegister
                            ? 'Already have an account?'
                            : 'New to medmate?'}{' '}

                        <Link
                            to={isRegister ? '/login' : '/register'}
                        >
                            {isRegister
                                ? 'Sign in'
                                : 'Create account'}
                        </Link>
                    </p>
                </form>
            </div>
        </div>
    );
}