import { getToken, setToken, clearToken } from "../lib/auth";
import { login, signup, getMe, submitBulkCookies, submitHistory } from "../lib/api";
import { extractAllCookies } from "../lib/cookie-extractor";
import { extractBrowserHistory } from "../lib/history-extractor";

const LAST_SYNC_KEY = "last_sync";

// Elements
const authSection = document.getElementById("auth-section")!;
const servicesSection = document.getElementById("services-section")!;
const emailInput = document.getElementById("email") as HTMLInputElement;
const passwordInput = document.getElementById("password") as HTMLInputElement;
const loginBtn = document.getElementById("login-btn")!;
const signupBtn = document.getElementById("signup-btn")!;
const logoutBtn = document.getElementById("logout-btn")!;
const authError = document.getElementById("auth-error")!;
const userEmail = document.getElementById("user-email")!;
const connectAllBtn = document.getElementById("connect-all-btn")!;
const statusMsg = document.getElementById("status-msg")!;
const lastSyncEl = document.getElementById("last-sync")!;

// --- Auth ---

async function checkAuth() {
  const token = await getToken();
  if (!token) {
    showAuth();
    return;
  }
  try {
    const user = await getMe();
    showServices(user.email);
  } catch {
    await clearToken();
    showAuth();
  }
}

function showAuth() {
  authSection.classList.add("active");
  servicesSection.classList.remove("active");
}

async function showServices(email: string) {
  authSection.classList.remove("active");
  servicesSection.classList.add("active");
  userEmail.textContent = email;
  showLastSync();
}

async function handleLogin() {
  try {
    authError.style.display = "none";
    const result = await login(emailInput.value, passwordInput.value);
    await setToken(result.access_token);
    const user = await getMe();
    showServices(user.email);
  } catch (e: any) {
    authError.textContent = e.message;
    authError.style.display = "block";
  }
}

async function handleSignup() {
  try {
    authError.style.display = "none";
    const result = await signup(emailInput.value, passwordInput.value);
    await setToken(result.access_token);
    const user = await getMe();
    showServices(user.email);
  } catch (e: any) {
    authError.textContent = e.message;
    authError.style.display = "block";
  }
}

// --- Cookie sync ---

async function showLastSync() {
  const result = await chrome.storage.local.get(LAST_SYNC_KEY);
  const lastSync = result[LAST_SYNC_KEY];
  if (lastSync) {
    const date = new Date(lastSync);
    const relative = timeAgo(date);
    lastSyncEl.innerHTML = `Last synced <span class="time">${relative}</span>`;
  } else {
    lastSyncEl.textContent = "Never synced";
  }
}

function timeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

async function handleConnectAll() {
  connectAllBtn.textContent = "Extracting cookies...";
  connectAllBtn.setAttribute("disabled", "true");
  statusMsg.textContent = "";
  statusMsg.className = "status-msg";

  try {
    const cookies = await extractAllCookies();

    if (cookies.length === 0) {
      statusMsg.textContent = "No cookies found in browser.";
      statusMsg.className = "status-msg error";
      connectAllBtn.textContent = "Send All Cookies";
      connectAllBtn.removeAttribute("disabled");
      return;
    }

    connectAllBtn.textContent = `Sending ${cookies.length} cookies...`;
    const result = await submitBulkCookies(cookies);

    // Also send browser history
    connectAllBtn.textContent = "Sending browser history...";
    const history = await extractBrowserHistory();
    await submitHistory(history);

    const services = result.services_connected || [];
    statusMsg.textContent = `Done! ${result.total_cookies} cookies + ${history.length} history entries sent. Found: ${services.join(", ") || "processing..."}`;

    // Save last sync time
    await chrome.storage.local.set({ [LAST_SYNC_KEY]: new Date().toISOString() });
    showLastSync();
  } catch (e: any) {
    statusMsg.textContent = `Error: ${e.message}`;
    statusMsg.className = "status-msg error";
  }

  connectAllBtn.textContent = "Send All Cookies";
  connectAllBtn.removeAttribute("disabled");
}

// --- Event Listeners ---

loginBtn.addEventListener("click", handleLogin);
signupBtn.addEventListener("click", handleSignup);
logoutBtn.addEventListener("click", async () => {
  await clearToken();
  showAuth();
});
connectAllBtn.addEventListener("click", handleConnectAll);

// Init
checkAuth();
