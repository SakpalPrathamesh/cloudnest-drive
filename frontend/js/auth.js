"use strict";

// ── Switch between Login and Signup tabs ──
function switchTab(tab) {
  clearAlerts();

  if (tab === "login") {
    document.getElementById("login-form").style.display  = "block";
    document.getElementById("signup-form").style.display = "none";
    document.getElementById("tab-login").classList.add("active");
    document.getElementById("tab-signup").classList.remove("active");
  } else {
    document.getElementById("login-form").style.display  = "none";
    document.getElementById("signup-form").style.display = "block";
    document.getElementById("tab-login").classList.remove("active");
    document.getElementById("tab-signup").classList.add("active");
  }
}

// ── Show error message ──
function showError(msg) {
  const box = document.getElementById("error-box");
  document.getElementById("error-text").textContent = msg;
  box.style.display = "block";
  document.getElementById("success-box").style.display = "none";
}

// ── Show success message ──
function showSuccess(msg) {
  const box = document.getElementById("success-box");
  document.getElementById("success-text").textContent = msg;
  box.style.display = "block";
  document.getElementById("error-box").style.display = "none";
}

// ── Hide both messages ──
function clearAlerts() {
  document.getElementById("error-box").style.display   = "none";
  document.getElementById("success-box").style.display = "none";
}

// ── Set button to loading state ──
function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  btn.disabled    = loading;
  btn.textContent = loading ? "Please wait…" : btn.dataset.label;
}

// ── Convert Firebase error codes to friendly messages ──
function friendlyError(code) {
  const messages = {
    "auth/invalid-email":       "Please enter a valid email address.",
    "auth/user-not-found":      "No account found with this email.",
    "auth/wrong-password":      "Incorrect password. Try again.",
    "auth/invalid-credential":  "Incorrect email or password.",
    "auth/email-already-in-use":"This email is already registered. Sign in instead.",
    "auth/weak-password":       "Password must be at least 6 characters.",
    "auth/too-many-requests":   "Too many attempts. Please wait a moment.",
    "auth/network-request-failed": "No internet connection.",
  };
  return messages[code] || "Something went wrong. Please try again.";
}

// ── Handle Login ──
async function handleLogin(event) {
  event.preventDefault();
  clearAlerts();

  const email    = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  if (!email || !password) {
    showError("Please fill in all fields.");
    return;
  }

  // Save button label and show loading
  const btn = document.getElementById("login-btn");
  btn.dataset.label = btn.textContent;
  setLoading("login-btn", true);

  try {
    // 1. Sign in with Firebase
    const userCredential = await window._signIn(
      window._auth, email, password
    );
    const user = userCredential.user;

    // 2. Get the ID token
    const idToken = await user.getIdToken();

    // 3. Verify token with our backend
    const res = await fetch(`${window._apiBase}/api/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Backend verification failed.");
    }

    // 4. Save token in sessionStorage (browser memory)
    sessionStorage.setItem("cloudnest_token", idToken);
    sessionStorage.setItem("cloudnest_user", JSON.stringify({
      uid:   user.uid,
      email: user.email,
      name:  user.displayName || user.email
    }));

    // 5. Redirect to drive page
    showSuccess("Signed in! Redirecting…");
    setTimeout(() => {
      window.location.href = "drive.html";
    }, 800);

  } catch (err) {
    const msg = err.code
      ? friendlyError(err.code)
      : (err.message || "Login failed.");
    showError(msg);
    setLoading("login-btn", false);
  }
}

// ── Handle Signup ──
async function handleSignup(event) {
  event.preventDefault();
  clearAlerts();

  const name     = document.getElementById("signup-name").value.trim();
  const email    = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value;

  if (!name || !email || !password) {
    showError("Please fill in all fields.");
    return;
  }
  if (password.length < 6) {
    showError("Password must be at least 6 characters.");
    return;
  }

  const btn = document.getElementById("signup-btn");
  btn.dataset.label = btn.textContent;
  setLoading("signup-btn", true);

  try {
    // 1. Create Firebase account
    const userCredential = await window._createUser(
      window._auth, email, password
    );
    const user = userCredential.user;

    // 2. Set display name
    await window._updateProfile(user, { displayName: name });

    // 3. Get ID token
    const idToken = await user.getIdToken();

    // 4. Verify with backend
    const res = await fetch(`${window._apiBase}/api/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Backend verification failed.");
    }

    // 5. Save and redirect
    sessionStorage.setItem("cloudnest_token", idToken);
    sessionStorage.setItem("cloudnest_user", JSON.stringify({
      uid:   user.uid,
      email: user.email,
      name:  name
    }));

    showSuccess("Account created! Redirecting…");
    setTimeout(() => {
      window.location.href = "drive.html";
    }, 800);

  } catch (err) {
    const msg = err.code
      ? friendlyError(err.code)
      : (err.message || "Signup failed.");
    showError(msg);
    setLoading("signup-btn", false);
  }
}