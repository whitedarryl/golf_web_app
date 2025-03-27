document.addEventListener("DOMContentLoaded", async () => {
    console.log("✅ Script is running!");

    const playerInput = document.getElementById("player-name");
    const dropdown = document.getElementById("player-dropdown");
    const scoreInputs = document.querySelectorAll(".score-input");
    const form = document.getElementById("scorecard-form");

    document.querySelectorAll(".score-input").forEach(input => {
        input.classList.add("handwritten");
    });

    // ✅ Debugging check: Ensure the form exists
    if (!form) {
        console.error("❌ ERROR: Form with ID 'scorecard-form' NOT FOUND!");
        return;
    }

    // ✅ Fetch player list from API (Only players without scores)
    let players = []; // Store the initial player list globally

    async function fetchPlayers() {
        try {
            const response = await fetch("/api/players");
            if (response.ok) {
                players = await response.json();
                console.log("✅ Players loaded:", players);
                updateDropdown(players); // ✅ Populate dropdown immediately
            } else {
                console.error("❌ Failed to load players:", await response.text());
            }
        } catch (error) {
            console.error("❌ Error fetching players:", error);
        }
    }    

    await fetchPlayers(); // ✅ Fetch players on page load

    // ✅ Show dropdown when input is clicked
    playerInput.addEventListener("focus", () => {
        dropdown.classList.remove("hidden");
        updateDropdown(players);
    });

    // ✅ Hide dropdown when clicking outside
    document.addEventListener("click", (event) => {
        if (!playerInput.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.classList.add("hidden");
        }
    });

    // ✅ Handle score input
    scoreInputs.forEach((input, index) => {
        input.addEventListener("input", (event) => {
            const value = event.target.value;

            // ✅ Move focus to the next input if a single digit is typed
            if (value.length === 1 && index < scoreInputs.length - 1) {
                scoreInputs[index + 1].focus();
            }

            updateTotals();
        });
    });

    // ✅ Handle form submission
    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        console.log("📤 Form submitted!");

        const playerName = playerInput.value.trim();
        let front9 = [], back9 = [];

        // ✅ Collect score data
        scoreInputs.forEach((input, index) => {
            const value = parseInt(input.value, 10) || 0;
            if (index < 9) front9.push(value);
            else back9.push(value);
        });

        if (!playerName) {
            alert("❌ Please enter a player name.");
            return;
        }

        const payload = { player: playerName, front_9: front9, back_9: back9 };
        console.log("📤 Submitting Scores:", payload);

        try {
            const response = await fetch("/api/submit_scores", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            console.log("✅ Server Response:", result);

            if (response.ok) {
                alert(result.message || "Scores saved!");
            
                // ✅ Remove the player from the dropdown list immediately
                players = players.filter(player => player !== playerName);
                updateDropdown(players); // ✅ Refresh dropdown without delay
            
                // ✅ Clear input fields
                playerInput.value = "";
                scoreInputs.forEach(input => {
                    input.value = "";
                });
            
                updateTotals(); // ✅ Reset totals to 0
            
                // ✅ Move focus back to the player name input for the next entry
                playerInput.focus();
            }
             else {
                console.error("❌ Error saving scores:", result.error);
            }
        } catch (error) {
            console.error("❌ Error submitting scores:", error);
        }
    });

    // ✅ Function to update totals
    function updateTotals() {
        let front9Total = 0;
        let back9Total = 0;

        document.querySelectorAll(".score-input").forEach((input, index) => {
            const val = parseInt(input.value, 10);
            if (!isNaN(val)) {
                if (index < 9) {
                    front9Total += val;
                } else {
                    back9Total += val;
                }
            }
        });

        const overallTotal = front9Total + back9Total;

        // Update "OUT", "IN", and "TOTAL" boxes
        document.getElementById("out-total").value = front9Total;
        document.getElementById("in-total").value = back9Total;
        document.getElementById("total-score").value = overallTotal;

        console.log(`📊 Updated Totals - OUT: ${front9Total}, IN: ${back9Total}, TOTAL: ${overallTotal}`);
    }

    // ✅ Filter players based on input
    playerInput.addEventListener("input", () => {
        const search = playerInput.value.toLowerCase();
        const filteredPlayers = players.filter(player => player.toLowerCase().includes(search));
        updateDropdown(filteredPlayers);
    });

    // ✅ Update dropdown list (only players without scores)
    function updateDropdown(playerList) {
        dropdown.innerHTML = "";
        if (playerList.length === 0) {
            dropdown.classList.add("hidden");
            return;
        }

        playerList.forEach(player => {
            const item = document.createElement("li");
            item.textContent = player;
            item.classList.add("p-2", "hover:bg-green-200", "cursor-pointer");
            item.addEventListener("click", () => {
                playerInput.value = player;
                dropdown.classList.add("hidden");
            });
            dropdown.appendChild(item);
        });

        dropdown.classList.remove("hidden");
    }
});
