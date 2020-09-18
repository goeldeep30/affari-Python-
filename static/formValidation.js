var check = function() {
    if (document.getElementById('inputPassword').value ==
      document.getElementById('inputRePassword').value) {
      document.getElementById('message').style.color = 'green';
      document.getElementById('message').innerHTML = '';
      document.getElementById("passwordResetSubmit").removeAttribute("disabled");
    } else {
      document.getElementById('message').style.color = 'red';
      document.getElementById('message').innerHTML = 'Password not matched';
      document.getElementById("passwordResetSubmit").setAttribute("disabled", "");
    }
  }