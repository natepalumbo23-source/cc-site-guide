(() => {
  const TOTAL = 6;
  const state = {
    step: 0,
    first_name: "",
    email: "",
    phone: "",
    where_now: "",
    school_or_title: "",
    hear_about: "",
  };

  const steps = [...document.querySelectorAll(".step")];
  const fill = document.getElementById("progress_fill");
  const label = document.getElementById("progress_label");

  function updateProgress() {
    const pct = ((state.step + 1) / TOTAL) * 100;
    fill.style.width = `${pct}%`;
    label.textContent = `Step ${state.step + 1} of ${TOTAL}`;
  }

  function showStep(i) {
    state.step = i;
    steps.forEach((el) => el.classList.toggle("active", Number(el.dataset.step) === i));
    updateProgress();
    const input = steps[i].querySelector("input");
    if (input) setTimeout(() => input.focus(), 50);
  }

  function adaptDetailCopy() {
    const q = document.getElementById("detail_question");
    const hint = document.getElementById("detail_hint");
    const kicker = document.getElementById("detail_kicker");
    const input = document.getElementById("school_or_title");
    const w = state.where_now;
    if (w === "Student") {
      kicker.textContent = "Background";
      q.textContent = "What School?";
      hint.textContent = "Full name is fine.";
      input.placeholder = "School name";
    } else if (w === "Career switcher") {
      kicker.textContent = "Background";
      q.textContent = "Current Role or Field?";
      hint.textContent = "Title or industry works.";
      input.placeholder = "Current role or field";
    } else {
      kicker.textContent = "Background";
      q.textContent = "Current Job Title?";
      hint.textContent = "Keep it short.";
      input.placeholder = "Job title";
    }
  }

  async function savePartial() {
    const answers = { ...state };
    delete answers.step;
    try {
      await fetch("/api/funnel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(answers),
      });
    } catch (_) {
      /* offline prototype: ignore */
    }
  }

  async function finish() {
    await savePartial();
    window.location.href = "/paywall";
  }

  async function nextFromText(requireSel) {
    if (requireSel) {
      const el = document.querySelector(requireSel);
      const val = (el.value || "").trim();
      if (!val) {
        el.focus();
        el.style.borderColor = "#C4553B";
        return;
      }
      el.style.borderColor = "";
      state[el.name] = val;
    } else {
      const phone = document.getElementById("phone");
      if (phone) state.phone = (phone.value || "").trim();
    }
    await savePartial();
    if (state.step >= TOTAL - 1) return finish();
    showStep(state.step + 1);
  }

  document.querySelectorAll("[data-next]").forEach((btn) => {
    btn.addEventListener("click", () => nextFromText(btn.dataset.require));
  });

  document.querySelectorAll("[data-skip]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      state.phone = "";
      await savePartial();
      showStep(state.step + 1);
    });
  });

  document.querySelectorAll(".choices").forEach((group) => {
    group.querySelectorAll(".choice").forEach((btn) => {
      btn.addEventListener("click", async () => {
        group.querySelectorAll(".choice").forEach((c) => c.classList.remove("selected"));
        btn.classList.add("selected");
        const key = group.dataset.key;
        state[key] = btn.dataset.value;
        if (key === "where_now") adaptDetailCopy();
        await savePartial();
        setTimeout(() => {
          if (state.step >= TOTAL - 1) finish();
          else showStep(state.step + 1);
        }, 140);
      });
    });
  });

  document.querySelectorAll(".field input").forEach((input) => {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const btn = input.parentElement.querySelector("[data-next]");
        if (btn) btn.click();
      }
    });
  });

  updateProgress();
})();
