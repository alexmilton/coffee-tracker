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

  document.querySelectorAll("[data-sortable-table]").forEach(function(table) {
    table.querySelectorAll(".sort-button").forEach(function(button) {
      button.addEventListener("click", function() {
        const sortKey = button.dataset.sortKey;
        const sortType = button.dataset.sortType || "text";
        const ascending = button.dataset.sortDirection !== "ascending";
        const rows = Array.from(table.tBodies[0].rows);

        rows.sort(function(rowA, rowB) {
          const cellA = rowA.querySelector(`[data-sort-key="${sortKey}"]`);
          const cellB = rowB.querySelector(`[data-sort-key="${sortKey}"]`);
          if (!cellA || !cellB) {
            return 0;
          }
          const valueA = cellA.dataset.sortValue || cellA.textContent.trim();
          const valueB = cellB.dataset.sortValue || cellB.textContent.trim();
          const comparison = sortType === "number"
            ? Number(valueA) - Number(valueB)
            : sortType === "date"
              ? valueA.localeCompare(valueB)
              : valueA.localeCompare(valueB, undefined, { sensitivity: "base" });

          return ascending ? comparison : -comparison;
        });

        rows.forEach(function(row) {
          table.tBodies[0].appendChild(row);
        });
        table.querySelectorAll(".sort-button").forEach(function(otherButton) {
          delete otherButton.dataset.sortDirection;
          otherButton.removeAttribute("aria-sort");
        });
        button.dataset.sortDirection = ascending ? "ascending" : "descending";
        button.setAttribute("aria-sort", button.dataset.sortDirection);
      });
    });
  });

  document.querySelectorAll("[data-purchase-row]").forEach(function(row) {
    const editButton = row.querySelector(".edit-purchase-button");
    const saveButton = row.querySelector(".save-purchase-button");
    const cancelButton = row.querySelector(".cancel-purchase-button");
    const deleteForm = row.querySelector(".delete-purchase-form");

    editButton.addEventListener("click", function() {
      row.classList.add("edit-mode");
      row.querySelectorAll(".purchase-display").forEach(function(element) {
        element.hidden = true;
      });
      row.querySelectorAll(".purchase-edit-input").forEach(function(element) {
        element.hidden = false;
      });
      editButton.hidden = true;
      saveButton.hidden = false;
      cancelButton.hidden = false;
      deleteForm.hidden = true;
    });

    cancelButton.addEventListener("click", function() {
      row.classList.remove("edit-mode");
      row.querySelectorAll(".purchase-display").forEach(function(element) {
        element.hidden = false;
      });
      row.querySelectorAll(".purchase-edit-input").forEach(function(element) {
        element.hidden = true;
      });
      editButton.hidden = false;
      saveButton.hidden = true;
      cancelButton.hidden = true;
      deleteForm.hidden = false;
    });

    deleteForm.addEventListener("submit", function(event) {
      if (!window.confirm("Delete this purchase?")) {
        event.preventDefault();
      }
    });
  });
});