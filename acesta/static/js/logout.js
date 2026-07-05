$(function () {
  $("a.logout-link").on("click", function (e) {
    try {
      window.sessionStorage.removeItem("acestaInterestRegionCardCompact");
    } catch (error) {
      // Logout must still work when browser storage is unavailable.
    }
    $("#LogoutForm").submit();
  });
});
