// Edit profile page — live avatar preview
const avatarInput = document.getElementById("id_avatar");
const avatarPreview = document.getElementById("avatarPreview");
const avatarPlaceholder = document.getElementById("avatarPlaceholder");

if (avatarInput) {
  avatarInput.addEventListener("change", function () {
    const file = this.files[0];
    if (file && file.type.startsWith("image/")) {
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
    }
  });
}