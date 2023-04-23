$(function () {
  $("a.logout-link").on("click", function (e) {
    $("#LogoutForm").submit();
  });
});
