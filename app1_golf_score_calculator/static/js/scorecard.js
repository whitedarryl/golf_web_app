document.addEventListener("DOMContentLoaded", function () {
  console.log("🔥 DOM ready. JS starting");

  // Debugging version - add this temporarily to your scorecard.js
  const isInvalidName = (name) => {
    console.log(`Validating: "${name}"`);
    
    if (!name || name.trim() === "") {
      console.log("Rejecting: empty name");
      return true;
    }
    
    if (/^x+$/i.test(name)) {
      console.log("Rejecting: matches /^x+$/i pattern");
      return true;
    }
    
    // Skip placeholder check for names from the player list
    if (playerNames.includes(name)) {
      console.log(`Name "${name}" is in player list - accepting`);
      return false;
    }
    
    // Check for common placeholders
    const placeholders = ["test", "dummy", "sample", "user", "player"];
    for (const placeholder of placeholders) {
      if (name.toLowerCase().includes(placeholder)) {
        console.log(`Rejecting: contains placeholder "${placeholder}"`);
        return true;
      }
    }
    
    console.log(`Name "${name}" is valid`);
    return false;
  };

  const playerInput = document.getElementById("playerName");
  const scoreInputs = Array.from(document.querySelectorAll(".score-input"));
  const submitButton = document.getElementById("submitBtn");
  const adminToggle = document.getElementById("adminToggle");
  const adminControls = document.getElementById("adminControls");
  const toast = document.getElementById("toast");
  const toggleBtn = document.getElementById("toggleSubmissionStatus");
  const statusSpan = document.getElementById("submissionStatus");
  let playerNames = [];
  let awesomplete = null;

  // Move refreshPlayerList inside DOMContentLoaded so it can access variables
  function refreshPlayerList() {
    fetch("/golf_score_calculator/get_names")
      .then(res => res.json())
      .then(names => {
        playerNames = names.slice();

        // Update Awesomplete
        if (awesomplete) {
          awesomplete.list = names;
        }

        // Don't update counter here - it should be updated by whoever calls this function
        // The counter is managed separately via get_counts or the response from add/remove

        console.log(`🔄 Refreshed player list: ${names.length} players`);
      })
      .catch(err => console.error("Failed to refresh player names:", err));
  }

  if (toggleBtn && statusSpan) {
    toggleBtn.addEventListener("click", () => {
      const isVisible = statusSpan.style.display !== "none";
      statusSpan.style.display = isVisible ? "none" : "inline";
    });

    // Show it by default
    statusSpan.style.display = "inline";
  }

  if (adminToggle && adminControls) {
    adminToggle.addEventListener("click", () => {
      const isVisible = adminControls.style.display === "block";
      adminControls.style.display = isVisible ? "none" : "block";
      adminToggle.textContent = isVisible ? "👀 Show Admin Controls" : "🙈 Hide Admin Controls";
    });
  }

  function showToast(message) {
    toast.textContent = message;
    toast.style.visibility = "visible";
    toast.style.opacity = 1;
    setTimeout(() => {
      toast.style.opacity = 0;
      toast.style.visibility = "hidden";
    }, 3000);
  }

  function calculateTotal(className, outputElement) {
    const inputs = document.querySelectorAll(`.score-input.${className}`);
    let total = 0;
    inputs.forEach((input) => {
      const value = parseInt(input.value, 10);
      if (!isNaN(value)) {
        total += value;   // ← now it accumulates properly
      }
    });
    outputElement.textContent = total;
    return total;
  }

  function updateTotals() {
    const out = calculateTotal("front", outTotal);
    const back = calculateTotal("back", inTotal);
    grandTotal.textContent = out + back;
  }

  function resetForm() {
    playerInput.value = "";
    scoreInputs.forEach((input) => (input.value = ""));
    outTotal.textContent = "0";
    inTotal.textContent = "0";
    grandTotal.textContent = "0";
    submitButton.disabled = true;
    playerInput.focus();
  }

  if (scoreInputs.length) {
    scoreInputs.forEach((input, idx) => {
      input.addEventListener("input", function () {
        const val = this.value;
        if (/^[1-8]$/.test(val)) {
          if (idx + 1 < scoreInputs.length) {
            scoreInputs[idx + 1].focus();
          }
        } else {
          this.value = "";
        }
        updateTotals();
      });

      input.addEventListener("keydown", function (e) {
        if (e.key === "Backspace") {
          if (this.value === "" && idx > 0) {
            scoreInputs[idx - 1].focus();
          }
        } else if (e.key === "Enter") {
          if (!submitButton.disabled) {
            submitButton.click();
          }
        }
      });
    });
  }

  if (playerInput && scoreInputs.length && submitButton) {
    submitButton.disabled = true;

    function checkFormValidity() {
      const nameValid = playerInput.value.trim().length > 0;
      const scoresFilled = Array.from(scoreInputs).some(
        (input) => input.value.trim() !== ""
      );
      submitButton.disabled = !(nameValid && scoresFilled);
    }

    playerInput.addEventListener("input", checkFormValidity);
    scoreInputs.forEach((input) => {
      input.addEventListener("input", checkFormValidity);
    });

    // —–––– Autocomplete setup –––––—  
    fetch("/golf_score_calculator/get_names")
      .then(res => res.json())
      .then(names => {
        playerNames = names.slice();
        awesomplete = new Awesomplete(playerInput, {
          list: names,
          minChars: 1,
          autoFirst: true,    // always highlight first suggestion
          tabSelect: true,    // let Tab pick it
          sort: Awesomplete.SORT_BYLENGTH
        });

        // Fetch actual count data on page load
        fetch("/golf_score_calculator/get_counts")
          .then(r => r.json())
          .then(ct => {
            console.log("🔍 JS - Received count data:", ct);
            const submittedEl = document.getElementById("submittedPlayers");
            const totalEl = document.getElementById("totalPlayers");
            const leftEl = document.querySelector(".players-left");
            console.log("🔍 JS - Found elements:", {submittedEl, totalEl, leftEl});

            if (submittedEl) submittedEl.textContent = ct.submitted;
            if (totalEl) totalEl.textContent = ct.total;
            if (leftEl) leftEl.textContent = `${ct.left} left`;

            console.log("🔍 JS - Updated display to:", {submitted: ct.submitted, total: ct.total, left: ct.left});
          })
          .catch(err => console.error("❌ Failed to load counts:", err));

        console.log(`✅ Autocomplete ready with ${names.length} names`);
      })
      .catch(err => console.error("Failed to load names:", err));


    // —–––– Submit scores handler –––––—  
    submitButton.addEventListener("click", async () => {
      // First, add validation for placeholder names
      const playerName = playerInput.value.trim();
      
      if (isInvalidName(playerName)) {
        showToast("❌ Please enter a valid player name");
        return;
      }
      
      // Continue with your existing code:
      // gather & validate
      const values = scoreInputs.map(i => parseInt(i.value) || null);
      if (values.includes(null)) {
        return showToast("❌ Invalid hole scores.");
      }

      // compute out/in/total
      const outScore = values.slice(0,9).reduce((a,b)=>a+b,0);
      const inScore  = values.slice(9).reduce((a,b)=>a+b,0);
      const total    = outScore + inScore;

      // name split
      const [first_name, ...rest] = playerInput.value.trim().split(" ");
      const last_name = rest.join(" ") || "";

      // pull course_id from hidden input
      const courseId = parseInt(
        document.getElementById("courseId").value, 10
      );

      // build payload
      const payload = {
        first_name,
        last_name,
        holes: values,
        out_score: outScore,
        in_score:  inScore,
        total,
        course_id: courseId
      };
      console.log("📤 Submitting:", payload);

      // POST to the same endpoint your real form uses
      fetch("/golf_score_calculator/submit", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(payload)
      })
      .then(response => {
        if (response.ok) {
          return response.json();
        } else {
          throw new Error("Network response was not ok.");
        }
      })
      .then(data => {
        // Remove the submitted player from the list
        const playerIndex = playerNames.indexOf(playerInput.value);
        if (playerIndex > -1) {
          playerNames.splice(playerIndex, 1);

          // Update the Awesomplete list
          if (awesomplete) {
            awesomplete.list = playerNames;
          }

          // Update the counter display using data from the response
          if (data.submitted_count !== undefined) {
            document.getElementById("submittedPlayers").textContent = data.submitted_count;
            document.getElementById("totalPlayers").textContent = data.total_count;
            document.querySelector(".players-left").textContent = `${data.players_left} left`;
          }
        }
        
        // Show success message and reset form
        showToast(data.message || "Score submitted successfully!");
        resetForm();
      })
      .catch(err => {
        console.error("Submission error:", err);
        showToast("❌ Submit failed.");
      });
    });

  } else {
    console.warn("⚠️ Missing required elements: playerInput, scoreInputs, or submitButton");
  } 

  // ─── Add Player handler ───
  document.getElementById("addPlayerBtn").addEventListener("click", async () => {
    const name = document.getElementById("newPlayerInput").value.trim();
    if (!name.includes(" ")) {
      return alert("Please enter full name (First Last)");
    }

    // Check for invalid names
    if (isInvalidName(name)) {
      return alert("❌ Invalid player name. Please enter a valid name.");
    }

    // 1) Tell the server to add the player
    let data;
    try {
      const res = await fetch("/admin_add_player", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: name.split(" ")[0],
          last_name:  name.split(" ").slice(1).join(" ")
        })
      });
      data = await res.json();
    } catch (err) {
      console.error("❌ Failed to add player:", err);
      return alert("❌ Failed to add player: " + err);
    }
    alert(data.message || "✅ Player added!");

    // Update counts from the response
    if (data.total_count !== undefined) {
      document.getElementById("submittedPlayers").textContent = data.submitted_count || 0;
      document.getElementById("totalPlayers").textContent = data.total_count || 0;
      document.querySelector(".players-left").textContent = `${data.players_left || 0} left`;
    }

    // Refresh player list
    refreshPlayerList();

    // 4) Auto‐select the newly‐added name and focus hole‐1
    playerInput.value = name;
    awesomplete.select();
    setTimeout(() => {
      document.getElementById("hole-1")?.focus();
    }, 0);

    // 5) Clear the "new player" box
    document.getElementById("newPlayerInput").value = "";
  });

  // ─── Remove Player handler ───
  document.getElementById("removePlayerBtn").addEventListener("click", async () => {
    const name = document.getElementById("newPlayerInput").value.trim();
    if (!name.includes(" ")) return alert("Please enter full name (First Last)");

    let data;
    try {
      const res = await fetch("/admin_remove_player", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: name })
      });
      data = await res.json();
    } catch (err) {
      console.error("❌ Remove player error:", err);
      return alert("❌ Failed to remove player: " + err);
    }

    alert(data.message || "✅ Player removed!");

    // Refresh player list
    refreshPlayerList();

    // Clear input fields
    document.getElementById("newPlayerInput").value = "";
    playerInput.value = "";
    playerInput.focus();

    // Update counts from the response (no need for extra fetch)
    if (data.total_count !== undefined) {
      document.getElementById("submittedPlayers").textContent = data.submitted_count || 0;
      document.getElementById("totalPlayers").textContent = data.total_count || 0;
      document.querySelector(".players-left").textContent = `${data.players_left || 0} left`;
    } else {
      // Fallback to fetching if backend doesn't return counts
      fetch("/golf_score_calculator/get_counts")
        .then(r => r.json())
        .then(ct => {
          document.getElementById("submittedPlayers").textContent = ct.submitted;
          document.getElementById("totalPlayers").textContent = ct.total;
          document.querySelector(".players-left").textContent = `${ct.left} left`;
        });
    }
  });

  const resetScoresBtn = document.getElementById("resetScoresBtn");
  if (resetScoresBtn) {
    resetScoresBtn.addEventListener("click", () => {
      if (!confirm("Are you sure you want to DELETE ALL SCORES?")) return;

      fetch("/golf_score_calculator/reset_scores", {
        method: "POST"
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("✅ All scores cleared.");
            window.location.reload();
          } else {
            console.error("Reset failed:", data.error);
            alert("❌ Failed to reset scores.");
          }
        })
        .catch(err => {
          console.error("Reset error:", err);
          alert("❌ Reset request failed.");
        });
    });
  }

  // Clear Fives Table Button
  const clearFivesBtn = document.getElementById("clearFivesBtn");
  if (clearFivesBtn) {
    clearFivesBtn.addEventListener("click", () => {
      if (!confirm("Are you sure you want to CLEAR THE FIVES TABLE?")) return;

      fetch("/golf_score_calculator/clear_fives", {
        method: "POST"
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("✅ Fives table cleared.");
          } else {
            console.error("Clear fives failed:", data.error);
            alert("❌ Failed to clear fives table.");
          }
        })
        .catch(err => {
          console.error("Clear fives error:", err);
          alert("❌ Clear fives request failed.");
        });
    });
  }

  // —–––– DEBUGGING Simulate Full Round –––––—
  const simulateBtn = document.getElementById("simulateBtn");
  console.log("🔍 simulateBtn ref:", simulateBtn);

  if (simulateBtn) {
    console.log("✅ Attaching click handler to simulateBtn");
    simulateBtn.addEventListener("click", async () => {
      console.log("🖱️ simulateBtn was clicked");

      // 1) re-fetch live player list
      let names = [];
      try {
        names = await fetch("/golf_score_calculator/get_names")
                     .then(r => r.json());
        console.log("🔄 fetched names:", names.length, names);
      } catch (e) {
        console.error("❌ fetch(get_names) failed:", e);
        return alert("❌ Unable to load players.");
      }
      if (!names.length) {
        console.log("ℹ️ No names returned, aborting simulate()");
        return alert("✅ No players to simulate!");
      }

      // 2) get course_id
      const courseId = parseInt(
        document.getElementById("courseId").value, 10
      );
      console.log("🎯 courseId =", courseId);
      if (!courseId) {
        return alert("❌ Missing course ID.");
      }

      // 3) Filter out invalid names
      const invalidNames = names.filter(name => isInvalidName(name));
      if (invalidNames.length > 0) {
        console.log("⚠️ These names were filtered out as invalid:", invalidNames);
      }
      const validNames = names.filter(name => !isInvalidName(name));
      console.log(`Filtered ${names.length} names to ${validNames.length} valid names`);
      
      if (names.length !== validNames.length) {
        console.log(`Skipped ${names.length - validNames.length} invalid names`);
      }

      // 4) loop & submit dummy data for valid names only
      for (let full_name of validNames) {
        const holes    = Array.from({ length: 18 }, () => Math.floor(Math.random() * 7) + 2);
        const outScore = holes.slice(0, 9).reduce((a,b)=>a+b,0);
        const inScore  = holes.slice(9).reduce((a,b)=>a+b,0);
        const total    = outScore + inScore;
        const [first_name,...rest] = full_name.split(" ");
        const last_name = rest.join(" ")||"";

        const payload = {
          first_name,
          last_name,
          holes,
          out_score: outScore,
          in_score: inScore,
          total,
          course_id: courseId
        };
        console.log("📦 Simulate payload:", payload);
        await fetch("/golf_score_calculator/submit", {
          method:  "POST",
          headers: {"Content-Type":"application/json"},
          body:    JSON.stringify(payload)
        });
      }

      console.log("✅ Simulation loop complete");
      alert(`✅ Dummy data submitted for ${validNames.length} players!`);
      
      // After simulation completes, update the counts
      fetch("/golf_score_calculator/get_counts")
        .then(r => r.json())
        .then(ct => {
          document.getElementById("submittedPlayers").textContent = ct.submitted;
          document.getElementById("totalPlayers").textContent = ct.total;
          document.querySelector(".players-left").textContent = `${ct.left} left`;
        });

      // Add this right after your simulation loop completes
      console.log("🔍 Checking for any missed players...");
      fetch("/golf_score_calculator/ensure_all_scores", { 
        method: "POST",
        headers: {
          'Content-Type': 'application/json'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.fixed_count > 0) {
          console.log(`⚠️ Fixed scores for ${data.fixed_count} missing players`);
        } else {
          console.log("✅ All players have scores");
        }
      })
      .catch(err => console.error("Error checking for missed players:", err));
    });
  } else {
    console.error("❌ simulateBtn not found in DOM!");
  }

  const exportBtn = document.getElementById("exportBtn");
  const progressBar = document.getElementById("exportBar");
  const exportProgress = document.getElementById("exportProgress");

  if (exportBtn && progressBar && exportProgress) {
    exportBtn.addEventListener("click", () => {
      exportBtn.disabled = true;
      exportProgress.style.display = "block";
      progressBar.value = 30;

      fetch("/golf_score_calculator/export_to_excel", { method: "POST" })
        .then(res => res.json())
        .then(data => {
          progressBar.value = 100;
          alert(data.message || "✅ Export complete!");
        })
        .catch(err => {
          console.error("❌ Export error:", err);
          alert("❌ Failed to export to Excel.");
        })
        .finally(() => {
          exportBtn.disabled = false;
          exportProgress.style.display = "none";
        });
    });
  } else {
    console.warn("⚠️ Export elements missing from DOM — export feature disabled.");
  }

  // ✅ Export to Archive Button Handler
  const exportArchiveBtn = document.getElementById("exportArchiveBtn");
  if (exportArchiveBtn) {
    console.log("✅ exportArchiveBtn found, attaching listener.");
    exportArchiveBtn.addEventListener("click", async () => {
      if (!confirm("📦 Export all scores to the archive table?")) return;

      console.log("📤 Sending export request...");
      try {
        const res = await fetch("/export_to_archive", { method: "POST" });
        const data = await res.json();
        console.log("✅ Export response:", data);
        alert(data.message || "✅ Export completed.");
      } catch (err) {
        console.error("❌ Export failed:", err);
        alert("❌ Export failed. Check console for details.");
      }
    });
  } else {
    console.error("❌ exportArchiveBtn not found in DOM.");
  }

  console.log("✅ scorecard.js initialization complete");
});
