//document.addEventListener('DOMContentLoaded',()=>{
$(document).ready(function(){
var socket=io.connect(location.protocol+'//'+document.domain+':'+location.port)
socket.on('connection',function(socket){
	console.log("Connected!!!!")
})
idcontact_sent=-1
$("#status-options ul li").click(function() {
	$("#profile-img").removeClass();
	$("#status-online").removeClass("active");
	$("#status-away").removeClass("active");
	$("#status-busy").removeClass("active");
	$("#status-offline").removeClass("active");
	$(this).addClass("active");
	
	if($("#status-online").hasClass("active")) {
		$("#profile-img").addClass("online");
	} else if ($("#status-away").hasClass("active")) {
		$("#profile-img").addClass("away");
	} else if ($("#status-busy").hasClass("active")) {
		$("#profile-img").addClass("busy");
	} else if ($("#status-offline").hasClass("active")) {
		$("#profile-img").addClass("offline");
	} else {
		$("#profile-img").removeClass();
	};
	
	$("#status-options").removeClass("active");
});

function newMessage() {
	message = $(".message-input input").val();
	if($.trim(message) == '') {
		return false;
	}
	console.log("Entro a socket Emit...")

	socket.emit('message', {msg:message});
	$('<li class="sent"><p>' + message + '</p></li>').appendTo($('.messages ul'));
	$('.message-input input').val(null);
	$('.contact.active .preview').html('<span>You: </span>' + message);
	$(".messages").animate({ scrollTop: 1580}, "fast");
};

$(window).on('keydown', function(e) {
  if (e.which == 13) {
    newMessage();
    return false;
  }
});
/*
	document.querySelector('#send_message').onclick=()=>{
		socket.send(document.querySelector('#text_message').value);
	}*/
	msgsent=""
	socket.on('privateMessage', msgsent=>{
		console.log("Mensaje llegado...")
		$('<li class="replies"><p>' + msgsent+ '</p></li>').appendTo($('.messages ul'));
		$('.message-input input').val(null);
		$('.contact.active .preview').html('<span>You: </span>' + msgsent);
		$(".messages").animate({ scrollTop: 1580}, "fast");
    });
});
function getContact(e,name){
	console.log('Usuario es :::'+e)
	idcontact_sent=e;
	document.getElementById("nameContact").innerHTML = name;
	$("#chatmessages").empty();
	$.ajax({
	type : "POST",
	url : '/setContactID',
	dataType: "json",
	data: JSON.stringify(e),
	contentType: 'application/json;charset=UTF-8',

	success: function (data) {
		var datamsg=JSON.parse(data);
		if(datamsg!=''){
		for(var k in datamsg){
			console.log('Print userfrom :::'+datamsg[k]['user_from'])
			if(e==parseInt(datamsg[k]['user_from']))
				$('<li class="replies"><p>' + datamsg[k]['content'] + '</p></li>').appendTo($('.messages ul'));
			else
				$('<li class="sent"><p>' + datamsg[k]['content']+ '</p></li>').appendTo($('.messages ul'));
		}
			$(".messages").animate({ scrollTop: 1580}, "fast");
			$('.contact.active .preview').html('<span>You: </span>' + msgsent);
			$('.message-input input').val(null);
		}
	}
	});
}