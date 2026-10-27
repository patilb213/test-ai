const TOKEN_KEY = "test_ai_token";

export function saveToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem(
      TOKEN_KEY,
      token
    );
  }
}

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(
    TOKEN_KEY
  );
}

export function logout() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(
      TOKEN_KEY
    );
  }
}

export function isLoggedIn() {
  return Boolean(getToken());
}