document.addEventListener("DOMContentLoaded", () => {
  const playerInput = document.getElementById("playerName");
  const submitBtn = document.getElementById("submitBtn");

  let allNames = [];
  let submittedNames = [];

  // ✅ Fetch and initialize Awesomplete
  fetch("/golf_score_calculator/get_names")
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        allNames = data.names;
        submittedNames = data.submitted_names || [];

        const availableNames = allNames.filter(
          (name) => !submittedNames.includes(name)
        );

        console.log("✅ Available:", availableNames);

        new Awesomplete(playerInput, {
          list: availableNames,
          minChars: 1,
          autoFirst: true,
        });
      } else {
        console.error("❌ Failed to load names:", data.message);
      }
    });

  // 👀 Enable submit only if valid name and scores are filled
  const inputs = document.querySelectorAll(".score-input");
  const progressBar = document.getElementById("progress-bar");

  function updateTotal(selector, outputId) {
    const inputs = document.querySelectorAll(selector);
    let total = 0;
    inputs.forEach((input) => {
      const val = parseInt(input.value, 10);
      if (!isNaN(val)) total += val;
    });
    document.getElementById(outputId).textContent = total;
    return total;
  }

  function checkForm() {
    const name = playerInput.value.trim();
    const hasName = name.length > 0;
    const hasScores = [...inputs].some((i) => i.value);
    submitBtn.disabled = !(hasName && hasScores);
  }

  inputs.forEach((input, idx) => {
    input.setAttribute("min", 1);
    input.setAttribute("max", 8);
    input.addEventListener("input", (e) => {
      const val = parseInt(e.target.value);
      if (!isNaN(val)) {
        if (val < 1 || val > 8) {
          e.target.value = "";
        } else {
          // Move to next box automatically
          if (idx < inputs.length - 1) inputs[idx + 1].focus();
        }
      }
      updateTotal(".score-input.front", "outTotal");
      updateTotal(".score-input.back", "inTotal");
      document.getElementById("grandTotal").textContent =
        updateTotal(".score-input.front", "outTotal") +
        updateTotal(".score-input.back", "inTotal");
      checkForm();
    });
  });

  playerInput.addEventListener("input", checkForm);

  submitBtn.addEventListener("click", () => {
    const name = playerInput.value.trim();
    const scores = [...inputs].map((i) => parseInt(i.value) || 0);
    const out = updateTotal(".score-input.front", "outTotal");
    const inn = updateTotal(".score-input.back", "inTotal");
    const total = out + inn;

    fetch("/golf_score_calculator/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, scores, out, inn, total }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showToast("✅ Score submitted!");
          playerInput.value = "";
          inputs.forEach((i) => (i.value = ""));
          document.getElementById("outTotal").textContent = "0";
          document.getElementById("inTotal").textContent = "0";
          document.getElementById("grandTotal").textContent = "0";
          checkForm();
          location.reload(); // ✅ Reload to refresh player list
        } else {
          alert("❌ Error: " + data.message);
        }
      })
      .catch((err) => {
        console.error(err);
        alert("❌ Unexpected error.");
      });
  });
});
