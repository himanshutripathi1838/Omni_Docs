import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../services/auth.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      const user = await registerUser(form);
      setUser(user);
      navigate("/dashboard");
    } catch {
      setError("Registration failed. Try another email.");
    }
  }

  return (
    <section className="auth-shell">
      <form className="auth-panel" onSubmit={handleSubmit}>
        <h1 className="text-3xl font-extrabold text-slate-950">Create your workspace</h1>
        <p className="mt-2 text-sm text-slate-600">Start with local MVP processing and history tracking.</p>
        {error && <p className="form-error">{error}</p>}
        <label className="form-label" htmlFor="name">Name</label>
        <input id="name" className="form-input" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
        <label className="form-label" htmlFor="email">Email</label>
        <input id="email" className="form-input" type="email" autoComplete="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
        <label className="form-label" htmlFor="password">Password</label>
        <input id="password" className="form-input" type="password" autoComplete="new-password" required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        <button className="btn-primary mt-6 w-full justify-center" type="submit">Register</button>
        <p className="mt-5 text-center text-sm text-slate-600">
          Already registered? <Link className="font-bold text-brand" to="/login">Login</Link>
        </p>
      </form>
    </section>
  );
}
