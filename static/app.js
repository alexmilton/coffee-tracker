document.addEventListener("DOMContentLoaded", function() {
  const purchaseDateInput = document.querySelector("#purchaseDate");
  if (purchaseDateInput) {
    flatpickr(purchaseDateInput, {
      allowInput: true,
      defaultDate: "today"
    });
  }

  const bagRows = document.querySelector("#bagRows");
  const addCoffeeButton = document.querySelector("#addCoffeeButton");

  if (bagRows && addCoffeeButton) {
    addCoffeeButton.addEventListener("click", function() {
      const rows = bagRows.querySelectorAll("[data-bag-row]");
      const newRow = rows[0].cloneNode(true);
      const rowNumber = rows.length + 1;

      newRow.querySelectorAll("input").forEach(function(input) {
        input.value = "";
        input.required = false;
      });
      newRow.querySelectorAll("label").forEach(function(label, index) {
        label.textContent = index === 0 ? `Coffee ${rowNumber}` : label.textContent;
      });
      newRow.querySelector(".remove-row-button").hidden = false;
      bagRows.appendChild(newRow);
    });

    bagRows.addEventListener("click", function(event) {
      if (event.target.classList.contains("remove-row-button")) {
        event.target.closest("[data-bag-row]").remove();
      }
    });
  }
});