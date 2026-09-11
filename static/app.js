document.addEventListener("DOMContentLoaded", function() {
  const purchaseDateInput = document.querySelector("#purchaseDate");
  if (purchaseDateInput) {
    flatpickr(purchaseDateInput, {
      allowInput: true,
      defaultDate: "today"
    });
  }
});