const simulateButton = document.getElementById("simulateFullRound");
if (simulateButton) {
  simulateButton.addEventListener("click", async () => {
  simulateButton.disabled = true;
  simulateButton.innerText = "Simulating...";

  const payload = {}; // stripped out course name/date

  try {
    const response = await fetch("/golf_score_calculator/run_tournament_scripts_v2", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.text();
    alert("✅ Tournament simulation finished!\n\n" + data);
  } catch (error) {
    alert("❌ Simulation failed: " + error);
  } finally {
    simulateButton.disabled = false;
    simulateButton.innerText = "Simulate Full Round";
  }
  });
}
