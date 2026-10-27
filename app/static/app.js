// Expand a row's notes when its name is clicked. The notes carry the caveats
// that make a price safe or unsafe to quote, so they live one click from the
// number rather than in a separate detail page.
document.addEventListener('click', function (event) {
  var toggle = event.target.closest('.name-toggle');
  if (!toggle) return;

  var row = toggle.closest('tr');
  var notesRow = row && row.nextElementSibling;
  if (!notesRow || !notesRow.classList.contains('notes-row')) return;

  var isOpen = notesRow.hasAttribute('hidden') === false;
  if (isOpen) {
    notesRow.setAttribute('hidden', '');
    toggle.setAttribute('aria-expanded', 'false');
  } else {
    notesRow.removeAttribute('hidden');
    toggle.setAttribute('aria-expanded', 'true');
  }
});
