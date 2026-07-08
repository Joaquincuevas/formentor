import { useState } from "react";
import api from "../api.js";

// Login con Google (stub): en desarrollo se ingresa el email directamente.
// En produccion, aqui iria el boton real de Google Identity y se enviaria el
// id_token al backend para verificarlo.
export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const { data } = await api.post("/auth/google/", { email });
      onLogin(data.token, data.user);
    } catch (err) {
      setError("No se pudo iniciar sesion");
    }
  };

  return (
    <div className="login-wrap">
      <div className="card">
        <h2>Casilleros Inteligentes</h2>
        <p style={{ color: "var(--muted)" }}>
          Inicia sesion con tu cuenta de Google (modo desarrollo: ingresa el email).
        </p>
        <form onSubmit={submit}>
          <label>Correo</label>
          <input type="email" value={email} required
                 onChange={(e) => setEmail(e.target.value)}
                 placeholder="tucorreo@uandes.cl" />
          <button className="btn" type="submit" style={{ width: "100%" }}>
            Continuar con Google
          </button>
        </form>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 16 }}>
          Superusuario demo: <b>admin</b> · Usuario demo: <b>demo@uandes.cl</b>
        </p>
      </div>
    </div>
  );
}
