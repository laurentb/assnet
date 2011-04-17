window.addEvent('domready', function() {
    var loginform = $('loginform');
    if (loginform) {
        $('login-link').addEvent('click', function(event) {
            event.stop();
            loginform.toggle();
            loginform.getElement('#login_username').focus();
        });
    }
});
