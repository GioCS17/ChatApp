var btnLogin=document.getElementById('btnSubmit')
var socket=io.connect(location.protocol+'//'+document.domain+':'+location.port)
btnLogin.addEventListener('click',function(){
    var username = $('#username').val();
    var credentials = {'username':username};
    socket.emit('addUserToRoom', credentials);
});

$(window).on('keydown', function(e) {
  if (e.which == 13) {
    console.log("Entro para setear usuario a join room ")
    var username = document.getElementById('username').value;
    console.log('valor de username '+username)
    var credentials = {'username':username};
    socket.emit('addUserToRoom', credentials);
    return false;
  }
});