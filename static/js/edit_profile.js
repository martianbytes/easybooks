// ─────────────────────────────────────────────────────────────
//  EasyBooks — Edit Profile Page JS
//  Handles: live avatar preview, bio char counter,
//           input focus styling, unsaved-changes warning
// ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function () {

  // ── 1. LIVE AVATAR PREVIEW ──────────────────────────────────
  // The avatar <input> is hidden; it's triggered by a <label>.
  // We watch it for changes and update the preview image.

  const avatarInput     = document.getElementById("id_avatar");
  const avatarPreview   = document.getElementById("avatarPreview");
  const avatarPlaceholder = document.getElementById("avatarPlaceholder");

  if (avatarInput) {
    avatarInput.addEventListener("change", function () {
      const file = this.files[0];
      if (!file || !file.type.startsWith("image/")) return;

      // Size guard — 2 MB
      if (file.size > 2 * 1024 * 1024) {
        showToast("Image must be under 2 MB.", "error");
        this.value = "";
        return;
      }

      const reader = new FileReader();
      reader.onload = function (e) {
        if (avatarPreview) {
          avatarPreview.src = e.target.result;
          avatarPreview.style.display = "block";
        }
        if (avatarPlaceholder) {
          avatarPlaceholder.style.display = "none";
        }
      };
      reader.readAsDataURL(file);
    });
  }


  // ── 2. BIO CHARACTER COUNTER ────────────────────────────────
  const bioField = document.getElementById("id_bio");

  if (bioField) {
    const MAX = 500;

    // Build counter element
    const counter = document.createElement("p");
    counter.className = "pdb-bio-counter";
    counter.style.cssText =
      "font-size:0.75rem; text-align:right; margin:4px 0 0; transition: color 0.2s;";
    bioField.parentNode.insertBefore(counter, bioField.nextSibling);

    function updateCounter() {
      const remaining = MAX - bioField.value.length;
      counter.textContent = remaining + " characters remaining";
      if (remaining < 0) {
        counter.style.color = "#9b2626";
      } else if (remaining < 50) {
        counter.style.color = "#c05e1e";
      } else {
        counter.style.color = "#98a8b4";
      }
    }

    bioField.addEventListener("input", updateCounter);
    updateCounter(); // init on load
  }


  // ── 3. INPUT FOCUS — add active class to pdb-input-wrap ─────
  // Gives the icon a colour tint when the field inside is focused.

  document.querySelectorAll(".pdb-input-wrap").forEach(function (wrap) {
    const field = wrap.querySelector("input, select, textarea");
    if (!field) return;

    field.addEventListener("focus", function () {
      wrap.classList.add("pdb-input-wrap--active");
    });
    field.addEventListener("blur", function () {
      wrap.classList.remove("pdb-input-wrap--active");
    });
  });


  // ── 4. UNSAVED CHANGES WARNING ──────────────────────────────
  // Warn the user if they try to leave with unsaved changes.

  const form = document.querySelector(".pdb-edit-form");
  let formDirty = false;

  if (form) {
    form.addEventListener("input", function () {
      formDirty = true;
    });

    // Clear the flag on intentional submit
    form.addEventListener("submit", function () {
      formDirty = false;
    });
  }

  window.addEventListener("beforeunload", function (e) {
    if (formDirty) {
      e.preventDefault();
      e.returnValue = "";
    }
  });


  // ── 5. SAVE BUTTON LOADING STATE ────────────────────────────
  // Shows a spinner-style label while the form is submitting.

  if (form) {
    form.addEventListener("submit", function () {
      const saveBtn = form.querySelector("button[type='submit']");
      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.style.opacity = "0.75";
        saveBtn.innerHTML =
          '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:pdb-spin 0.8s linear infinite"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg> Saving…';
      }
    });
  }


  // ── 6. TOAST HELPER ─────────────────────────────────────────

  function showToast(message, type) {
    type = type || "info";
    let toast = document.createElement("div");
    toast.textContent = message;
    toast.style.cssText = [
      "position:fixed",
      "bottom:24px",
      "right:24px",
      "z-index:9999",
      "padding:12px 20px",
      "border-radius:10px",
      "font-size:0.85rem",
      "font-family:inherit",
      "font-weight:500",
      "box-shadow:0 4px 16px rgba(0,0,0,.15)",
      "transition:opacity 0.3s",
      "opacity:0",
      type === "error"
        ? "background:#fde8e8;color:#9b2626;border:1px solid #f5c6c6"
        : "background:#e8f5ee;color:#2a6b41;border:1px solid #b6dfc8",
    ].join(";");

    document.body.appendChild(toast);
    requestAnimationFrame(function () { toast.style.opacity = "1"; });

    setTimeout(function () {
      toast.style.opacity = "0";
      setTimeout(function () { toast.remove(); }, 300);
    }, 3500);
  }

});


// ── Spin keyframe injected once ──────────────────────────────
(function () {
  if (document.getElementById("pdb-spin-style")) return;
  var style = document.createElement("style");
  style.id = "pdb-spin-style";
  style.textContent =
    "@keyframes pdb-spin { to { transform: rotate(360deg); } }" +
    ".pdb-input-wrap--active .pdb-input-icon { stroke: #c05e1e; }";
  document.head.appendChild(style);
})();