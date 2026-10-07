// Framer's form backend is gone with the paid plan: hand form submissions to the
// visitor's mail app instead. Capture phase runs before Framer's React handler.
window.addEventListener("submit", function (event) {
  var form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  var data = new FormData(form);
  var name = data.get("Name") || "";
  var email = data.get("Email") || "";
  var message = data.get("Message") || "";
  var subject = "ProtonMob contact" + (name ? " - " + name : "");
  var body = message + "\n\n" + name + (email ? " <" + email + ">" : "");
  window.location.href = "mailto:support@protonmob.com?subject=" +
    encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
}, true);
