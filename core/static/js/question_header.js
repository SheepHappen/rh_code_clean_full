function openQuestionSet(evt, questionSet) {
    $('#social').hide();
    $('#governance').hide();
    $('#environmental').hide();
    $('.environmental-tab').removeClass('environmental-tab-active');
    $('.social-tab').removeClass('social-tab-active');
    $('.governance-tab').removeClass('governance-tab-active');
    $('.no-mandatory-questions-msg').addClass('d-none');

    if ($('.social-tab').hasClass('disabledTab')) {
        $('.social-default').css({fill:"#949494"})
    }  else {
        $('.social-default').css({fill:"#ac554b"});
    }
    if ($('.governance-tab').hasClass('disabledTab')) {
        $('.governance-default').css({fill:"#949494"})
    } else {
        $('.governance-default').css({fill:"#3b64a2"});
    }
    if ($('.environmental-tab').hasClass('disabledTab')) {
        $('.environmental-default').css({fill:"#949494"})
    } else {
        $('.environmental-default').css({fill:"#006a4d"});
    }

    if (questionSet == 'social') {
        $('#social').show();
        $('.social-tab').addClass('social-tab-active');
        $('.social-default').css({fill:"#fff"});
        return;
    }
    if (questionSet == 'governance') {
        $('#governance').show();
        $('.governance-tab').addClass('governance-tab-active');
        $('.governance-default').css({fill:"#fff"});
        return;
    }
    if (questionSet == 'environmental') {
        $('#environmental').show();
        $('.environmental-tab').addClass('environmental-tab-active');
        $('.environmental-default').css({fill:"#fff"});
        return;
    }
}