import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { loginUser } from "../services/auth.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      const user = await loginUser(form);
      setUser(user);
      navigate("/dashboard");
    } catch {
      setError("Login failed. Check your email and password.");
    }
  }

  return (
    <section className="auth-shell">
      <form className="auth-panel" onSubmit={handleSubmit}>
        <h1 className="text-3xl font-extrabold text-slate-950">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-600">Sign in to continue processing documents.</p>
        {error && <p className="form-error">{error}</p>}
        <label className="form-label" htmlFor="email">Email</label>
        <input id="email" className="form-input" type="email" autoComplete="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
        <label className="form-label" htmlFor="password">Password</label>
        <input id="password" className="form-input" type="password" autoComplete="current-password" required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        <button className="btn-primary mt-6 w-full justify-center" type="submit">Login</button>
        <p className="mt-5 text-center text-sm text-slate-600">
          New to OmniDocs? <Link className="font-bold text-brand" to="/register">Create account</Link>
        </p>
      </form>
    </section>
  );
}
