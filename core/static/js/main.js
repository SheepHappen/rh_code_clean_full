$(document).ready(function() {

	var addRoundedImageWrapper = function () {
		$(".img-rounded").each(function() {
			if(!$(this).parent().hasClass('rounded-image')) {
				var $el = $('<div class="rounded-image"></div>');
				$(this).after($el);
				$el.append($(this));
				$el.height($el.width());
			}
		});
	};

	addRoundedImageWrapper();
	$('.selectmultiple').select2({ });
	$('.select').select2();

	$('[data-toggle="custom-collapse"]').on('click', function() {
		var menu = $($(this).data('target'));
		if ($( "header" ).hasClass('scrolled-down')) {
			$( "header" ).removeClass('scrolled-down');
		}
		if ($( "header" ).hasClass('scrolled-up')) {
			$( "header" ).removeClass('scrolled-up');
		}
		if ($('.navbar-toggler').hasClass('move-right')) {
			$('.navbar-toggler').removeClass('move-right');

			$('.mobile-header-column').animate({"left":"0px"}, 350);
			$('#page-wrapper').animate({"left":"0px"}, 350);
		} else {
			$('.navbar-toggler').addClass('move-right');

			$('.mobile-header-column').animate({"left":"300px"}, 350);
			$('#page-wrapper').animate({"left":"300px"}, 350);
		}
		menu.animate({'width':'toggle'}, 350);
	});
	$('body').css('padding-top', $('.navbar').outerHeight() + 'px');

	// detect scroll top or down
	if ($('.smart-scroll').length > 0) {
		var last_scroll_top = 0;
		$(window).on('scroll', function() {
			if ($('.mobile-user-icon').is(":visible")) {
				if ($('.navbar-toggler').hasClass('move-right')) {
					$('.navbar-toggler').trigger( "click" );
				}
				scroll_top = $(this).scrollTop();
				if(scroll_top < last_scroll_top) {
					$('.smart-scroll').removeClass('scrolled-down').addClass('scrolled-up');
				} else {
					$('.smart-scroll').removeClass('scrolled-up').addClass('scrolled-down');
				}
				last_scroll_top = scroll_top;
			}
		});
	}

	$('.radio-card').on('click', function() {
		var radio = $(this).find("input[type='radio']");
		radio.prop("checked", true).trigger('change');
	});

	var invalidIcon = function () {
		var errorId = $( ".is-invalid" ).attr('id');

		$( ".is-invalid" ).after( "<span class='form-error-icon "+ errorId  +"'></span>" );
		$( "." + errorId).css('margin-left', $( ".is-invalid" ).width() + 20 + 'px');
	}

	if ($('.textInput').hasClass( "is-invalid" )) {
		invalidIcon();
	}

	$('.show-hide-password a').click(function () {
		var icon = $(this).find('.toggle-password');
        if ($(icon).hasClass('fa-eye')) {
            $(this).parent().siblings('input').attr('type', 'text');
        } else {
            $(this).parent().siblings('input').attr('type', 'password');
        }
		$(icon).toggleClass('fa-eye').toggleClass('fa-eye-slash');
    });
});
