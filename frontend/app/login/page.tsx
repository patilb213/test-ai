"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "../../lib/api";
import { saveToken } from "../../lib/auth";

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    name: string;
    email: string;
  };
}

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");

    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);

    try {
      const data: LoginResponse = await api("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      // Save the JWT token
      saveToken(data.access_token);

      // Redirect to dashboard after successful login
      router.push("/dashboard");

      // Make sure the browser finishes the navigation
      router.refresh();
    } catch (err) {
      console.error("Login error:", err);

      let message = "Login failed. Please check your email and password.";

      if (err instanceof Error && err.message) {
        try {
          const parsed = JSON.parse(err.message);

          if (parsed.detail) {
            message = parsed.detail;
          }
        } catch {
          if (err.message.length < 200) {
            message = err.message;
          }
        }
      }

      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        background:
          "radial-gradient(circle at 70% 0%, rgba(139,124,246,0.12), transparent 35%), #07090d",
        color: "#f5f7fa",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "430px",
          background: "#0d1117",
          border: "1px solid #222936",
          borderRadius: "18px",
          padding: "36px",
          boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
        }}
      >
        {/* Header */}
        <div style={{ marginBottom: "30px" }}>
          <h1
            style={{
              margin: 0,
              fontSize: "32px",
              fontWeight: 700,
              letterSpacing: "-0.5px",
            }}
          >
            Test AI
          </h1>

          <p
            style={{
              marginTop: "10px",
              marginBottom: 0,
              color: "#8992a3",
              fontSize: "15px",
              lineHeight: 1.6,
            }}
          >
            AI-assisted smart test recording and verification
          </p>
        </div>

        <h2
          style={{
            margin: "0 0 8px",
            fontSize: "24px",
            fontWeight: 600,
          }}
        >
          Login
        </h2>

        <p
          style={{
            margin: "0 0 24px",
            color: "#8992a3",
            fontSize: "14px",
          }}
        >
          Sign in to continue to your testing dashboard.
        </p>

        {/* Error */}
        {error && (
          <div
            style={{
              marginBottom: "20px",
              padding: "12px 14px",
              borderRadius: "10px",
              border: "1px solid rgba(248,113,113,0.35)",
              background: "rgba(248,113,113,0.08)",
              color: "#f87171",
              fontSize: "14px",
              lineHeight: 1.5,
            }}
          >
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin}>
          {/* Email */}
          <div style={{ marginBottom: "18px" }}>
            <label
              htmlFor="email"
              style={{
                display: "block",
                marginBottom: "8px",
                fontSize: "14px",
                fontWeight: 500,
                color: "#d7dce5",
              }}
            >
              Email
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter your email"
              autoComplete="email"
              disabled={loading}
              style={{
                width: "100%",
                height: "48px",
                padding: "0 14px",
                borderRadius: "10px",
                border: "1px solid #222936",
                background: "#121720",
                color: "#f5f7fa",
                outline: "none",
              }}
            />
          </div>

          {/* Password */}
          <div style={{ marginBottom: "22px" }}>
            <label
              htmlFor="password"
              style={{
                display: "block",
                marginBottom: "8px",
                fontSize: "14px",
                fontWeight: 500,
                color: "#d7dce5",
              }}
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              disabled={loading}
              style={{
                width: "100%",
                height: "48px",
                padding: "0 14px",
                borderRadius: "10px",
                border: "1px solid #222936",
                background: "#121720",
                color: "#f5f7fa",
                outline: "none",
              }}
            />
          </div>

          {/* Login Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              height: "48px",
              border: "none",
              borderRadius: "10px",
              background: loading ? "#5f56ad" : "#8b7cf6",
              color: "#ffffff",
              fontSize: "15px",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.8 : 1,
              transition: "all 0.2s ease",
            }}
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        {/* Signup */}
        <div
          style={{
            marginTop: "24px",
            textAlign: "center",
            color: "#8992a3",
            fontSize: "14px",
          }}
        >
          Don't have an account?{" "}
          <button
            type="button"
            onClick={() => router.push("/signup")}
            style={{
              border: "none",
              background: "transparent",
              color: "#8b7cf6",
              fontWeight: 600,
              cursor: "pointer",
              padding: 0,
            }}
          >
            Create account
          </button>
        </div>
      </div>
    </main>
  );
}