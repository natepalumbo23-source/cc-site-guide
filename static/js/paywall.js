(() => {
  const form = document.getElementById("pay_form");
  const err = document.getElementById("pay_error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.textContent = "";
    const email = document.getElementById("pay_email").value.trim();
    const password = document.getElementById("pay_password").value;

    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;

    try {
      const res = await fetch("/api/account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, mock_pay: true }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        err.textContent = data.error || "Something went wrong.";
        btn.disabled = false;
        return;
      }
      window.location.href = data.redirect || "/home";
    } catch (_) {
      err.textContent = "Could not reach the server.";
      btn.disabled = false;
    }
  });
})();
