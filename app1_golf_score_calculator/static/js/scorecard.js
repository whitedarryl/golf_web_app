document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll(".score-input");
  const outTotalEl = document.getElementById("outTotal");
  const inTotalEl = document.getElementById("inTotal");
  const grandTotalEl = document.getElementById("grandTotal");
  const submitBtn = document.getElementById("submitBtn");
  const playerInput = document.getElementById("playerName");
  const progressEl = document.getElementById("progress");

  refreshPlayerOptions();
  updateTotals();

  window.addEventListener("load", () => {
    playerInput.focus();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !submitBtn.disabled) {
      e.preventDefault();
      submitBtn.click();
    }
  });

  function refreshPlayerOptions() {
    progressEl.style.opacity = 1;
    progressEl.textContent = "⏳ Loading players...";

    fetch("/score-calc/get_names")
      .then(res => res.json())
      .then(data => {
        console.log("🔍 GET /get_names response:", data);

        if (data.success) {
          if (!window.awesompleteInstance) {
            window.awesompleteInstance = setupAwesomplete(playerInput, data.names);
          } else {
            window.awesompleteInstance.list = data.names;
          }

          const submitted = data.total - data.names.length;
          const left = data.total - data.submitted;
          const percent = (data.submitted / data.total) * 100;

          const bar = document.getElementById("progress-bar");
          document.documentElement.style.setProperty('--progress-fill', `${percent}%`);

          if (percent >= 100) {
            bar.classList.add("flash");
          } else {
            bar.classList.remove("flash");
          }

          progressEl.innerHTML = `${data.submitted} of ${data.total} players submitted | <span class="players-left">${left} left</span>`;
          progressEl.style.opacity = 1;
          document.documentElement.style.setProperty('--progress-fill', `${percent}%`);
        } else {
          console.warn("⚠️ Server returned an error:", data.message);
          progressEl.textContent = "⚠️ Failed to load players.";
        }
      })
      .catch(err => {
        console.error("❌ Fetch error:", err);
        progressEl.textContent = "❌ Error loading player list.";
      });
  }

  function setupAwesomplete(input, names) {
    const awesomplete = new Awesomplete(input, {
      list: names,
      minChars: 1,
      autoFirst: true
    });

    let tabPressed = false;

    input.addEventListener("keydown", e => {
      if (e.key === "Tab") tabPressed = true;
    });

    input.addEventListener("blur", () => {
      if (tabPressed && awesomplete.ul.querySelectorAll("li").length) {
        awesomplete.select(awesomplete.ul.querySelector("li"));
        setTimeout(() => {
          const firstScoreInput = document.querySelector(".score-input");
          if (firstScoreInput) firstScoreInput.focus();
        }, 50);
      }
      tabPressed = false;
    });

    input.addEventListener("keydown", e => {
      if (e.key === "Enter") {
        const items = awesomplete.ul.querySelectorAll("li");
        if (items.length) {
          awesomplete.select(items[0]);
          e.preventDefault();
          setTimeout(() => {
            const firstScoreInput = document.querySelector(".score-input");
            if (firstScoreInput) firstScoreInput.focus();
          }, 50);
        }
      }
    });

    return awesomplete;
  }

  function calcTotal(inputs) {
    return Array.from(inputs)
      .map(input => parseInt(input.value) || 0)
      .reduce((a, b) => a + b, 0);
  }

  function updateTotals() {
    const frontInputs = document.querySelectorAll(".score-input.front");
    const backInputs = document.querySelectorAll(".score-input.back");

    const out = calcTotal(frontInputs);
    const inn = calcTotal(backInputs);

    outTotalEl.textContent = out;
    inTotalEl.textContent = inn;
    grandTotalEl.textContent = out + inn;

    checkIfAllFilled();
  }

  function checkIfAllFilled() {
    const allFilled = Array.from(inputs).every(
      input => /^[1-8]$/.test(input.value)
    );
    submitBtn.disabled = !allFilled || !playerInput.value.trim();
  }

  function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3000);
  }

  function clearForm() {
    inputs.forEach(input => input.value = "");
    playerInput.value = "";
    updateTotals();
  }

  inputs.forEach((input, index) => {
    input.addEventListener("input", e => {
      const val = e.target.value;

      if (!/^[1-8]$/.test(val)) {
        e.target.value = "";
        return;
      }

      if (index + 1 < inputs.length) {
        inputs[index + 1].focus();
      }

      updateTotals();
    });

    input.addEventListener("keydown", e => {
      if (e.key === "Backspace" && !e.target.value && index > 0) {
        inputs[index - 1].focus();
      }
    });

    input.addEventListener("paste", e => e.preventDefault());
  });

  playerInput.addEventListener("input", checkIfAllFilled);

  submitBtn.addEventListener("click", () => {
    const playerName = playerInput.value.trim();
    if (!playerName) {
      alert("Please select a player.");
      return;
    }

    const scores = Array.from(inputs).map(
      input => parseInt(input.value) || 0
    );

    const out = parseInt(outTotalEl.textContent);
    const inn = parseInt(inTotalEl.textContent);
    const total = parseInt(grandTotalEl.textContent);

    fetch("/score-calc/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: playerName,
        scores,
        out,
        inn,
        total
      })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast("✅ Score submitted!");
          document.getElementById("submitStatus").style.display = "block";

          progressEl.classList.remove("animated");
          void progressEl.offsetWidth;
          progressEl.classList.add("animated");

          setTimeout(() => {
            document.getElementById("submitStatus").style.display = "none";
          }, 3000);

          refreshPlayerOptions();
          clearForm();
          playerInput.focus();
        } else {
          alert("❌ Error: " + data.message);
        }
      })
      .catch(err => {
        console.error(err);
        alert("❌ Unexpected error.");
      });
  });
});
