/**
 * @author Xin Li <helloimlixin@gmail.com>
 * @file Description
 * @desc Created on 2020-06-15 2:38:08 pm
 * @copyright Xin Li
 */
$(function(){
	$('.btn#button-crawler').click(function(){
		if($(this).hasClass('active')){
			$(this).removeClass('active');
			$.ajax({
				url: '/crawler',
				data: 'stop',
				type: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				success: function(response){
					window.location.href = "/";
					console.log(response);
				},
				error: function(error){
					console.log(error);
				}
			});
		} else{
			$(this).addClass('active');

			$.ajax({
				url: '/crawler',
				data: $('form#crawler').serialize(),
				type: 'POST',
				success: function(response){
					console.log(response);
				},
				error: function(error){
					console.log(error);
				}
			});
		}
	});
});