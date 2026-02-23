$(document).ready(function() {

    var getQestionsRequiredCount = function (targetCls) {
        var hasRequiredCount = 0
        $('.' + targetCls).each(function() {
            if ($(this).hasClass('empty-question')) {
                return;
            }
            if (!$(this).hasClass('is-optional')) {
                hasRequiredCount += 1;
            }
        });
        return hasRequiredCount
    }

    var getQestionsOptionalCount = function (targetCls) {
        var hasOptionalCount = 0
        $('.' + targetCls).each(function() {
            if ($(this).hasClass('empty-question')) {
                return;
            }
            if ($(this).hasClass('is-optional')) {
                hasOptionalCount += 1;
            }
        });
        return hasOptionalCount
    }

    var requiredQuestionCountlabelUpdate = function () {
        var socialCount = getQestionsRequiredCount('social-question');
        $('.socialQuestionLength').html('(' + socialCount + ')');
        var govCount = getQestionsRequiredCount('governance-question');
        $('.govQuestionLength').html('(' + govCount + ')');
        var envCount = getQestionsRequiredCount('environmental-question');
        $('.envQuestionLength').html('(' + envCount + ')');
    }

    var allQuestionCountlabelUpdate = function () {
        var socialCount = getQestionsRequiredCount('social-question') + getQestionsOptionalCount('social-question');
        $('.socialQuestionLength').html('(' + socialCount + ')');
        var govCount = getQestionsRequiredCount('governance-question') + getQestionsOptionalCount('governance-question');
        $('.govQuestionLength').html('(' + govCount + ')');
        var envCount = getQestionsRequiredCount('environmental-question') + getQestionsOptionalCount('environmental-question');
        $('.envQuestionLength').html('(' + envCount + ')');
    }

    var hideOptional = true;
    $('.is-optional').each(function() {
        if ($(this).hasClass('has-answer')) {
            hideOptional = false;
        }
    });
    if (hideOptional) {
        $('.is-optional').hide();
    } else {
        $( ".toggle-optional").prop('checked', true);
        $('.toggle-optional').addClass('use-optional');
    }

    var disableEnvironmental = true;
    var environmentalHasOptional = false;

    $('.environmental-question').each(function() {
        if ($(this).hasClass('is-optional')) {
            environmentalHasOptional = true;
        } else {
            $('.environmental-tab').addClass('hasRequiredQuestions');
            disableEnvironmental = false;
        }
    });

    if (environmentalHasOptional) {
        $('.environmental-tab').addClass('hasOptionalQuestions');
    }
    if (disableEnvironmental && !$('.toggle-optional').hasClass('use-optional')) {
        $('.environmental-tab').addClass('disabledTab');
    }

    disableSocial = true;
    SocialHasOptional = false;

    $('.social-question').each(function() {
        if ($(this).hasClass('is-optional')) {
            SocialHasOptional = true;
        } else {
            $('.social-tab').addClass('hasRequiredQuestions');
            disableSocial = false;
        }
    });

    if (SocialHasOptional) {
        $('.social-tab').addClass('hasOptionalQuestions');
    }
    if (disableSocial && !$('.toggle-optional').hasClass('use-optional')) {
        $('.social-tab').addClass('disabledTab');
    }

    disableGov = true;
    GovHasOptional = false;

    $('.governance-question').each(function() {
        if ($(this).hasClass('is-optional')) {
            GovHasOptional = true;
        } else {
            $('.governance-tab').addClass('hasRequiredQuestions');
            disableGov = false;
        }
    });

    if (GovHasOptional) {
        $('.governance-tab').addClass('hasOptionalQuestions');
    }
    if (disableGov && !$('.toggle-optional').hasClass('use-optional')) {
        $('.governance-tab').addClass('disabledTab');
    }

    var clickTab = false;
    $('.tab-item').each(function() {
        if (clickTab == false) {
            if (!$(this).hasClass('disabledTab')) {
                $(this).click();
                clickTab = true;
            }
            if (clickTab) {
                return;
            }
        }
    });

    if (clickTab == false) {
        $('.no-mandatory-questions-msg').removeClass('d-none');
    }

    if ($('.toggle-optional').hasClass('use-optional')) {
        allQuestionCountlabelUpdate();
    } else {
        requiredQuestionCountlabelUpdate();
    }

    var drop = $('#dropzone').html();
    $('.failed-import').hide();
    $("#fileUpload").dropzone({
        previewTemplate: drop,
        success: function(file, response) {
            $('.failed-import').hide();
            $('#records').addClass('d-none');
            if (response.status == 'FAIL') {
                $('#template-preview').first().remove();
                $('.failed-import').show();
            }
            if (response.status == 'partial-upload') {
                $('#template-preview').first().remove();
                $('#records').removeClass('d-none');
                $.each(response.failed, function(index, value) {
                    $('#records > tbody').append("<tr>");
                    var tableRow = $("#records").find("tr").last();

                    tableRow.append(
                        "<td class='row-text-item'>" +
                            "<div>" +
                                value +
                            "</div>" +
                        "</td>"
                    );

                });
            }
            if (response.status == 'OK') {
                location.reload();
            }
        }
    });
    $('.open-file-dialog').on('click', function() {
        $('#file-input').trigger('click');
    });
    var postData = function(formData) {
        var token = $("input[name='csrfmiddlewaretoken']").prop("value");
        $.ajax({
            type: "POST",
            url: $('#fileUpload').attr('action'),
            data: formData,
            contentType: false,
            processData: false,
            beforeSend : function(jqXHR, settings) {
                jqXHR.setRequestHeader("x-csrftoken", token);
            },
        }).done(function( response ) {
            $('.failed-import').hide();
            if (response.status == 'FAIL') {
                $('#template-preview').first().remove();
                $('.failed-import').show();
            }
            if (response.status == 'OK') {
                location.reload();
            }
        });
    }
    $("input:file").change(function () {
        var uploadFile = $("input[name=file]")[0].files[0];
        var formData = new FormData();
        formData.append("file", uploadFile, uploadFile.name);
        formData.append("upload_file", true);
        postData(formData);
    });
    var toggleTabColours = function () {
        $('.no-mandatory-questions-msg').addClass('d-none');
        var hasRequiredCount = 0;
        if ($('.social-tab').hasClass('disabledTab')) {
            $('.social-default').css({fill:"#949494"});
            if ( $('.social-tab').hasClass('social-tab-active')) {
                hasRequiredCount += getQestionsRequiredCount('social-question');
                if (hasRequiredCount == 0) {
                    $('.no-mandatory-questions-msg').removeClass('d-none');
                }
                return;
            }
        }  else {
            if ($('.social-tab').hasClass('social-tab-active')) {
                $('.social-default').css({fill:"#fff"});
            } else {
                $('.social-default').css({fill:"#ac554b"});
            }
        }
        if ($('.governance-tab').hasClass('disabledTab')) {
            $('.governance-default').css({fill:"#949494"});

        } else {
            if ($('.governance-tab').hasClass('governance-tab-active')) {
                $('.governance-default').css({fill:"#fff"});
                if ( $('.governance-tab').hasClass('governance-tab-active')) {
                    hasRequiredCount += getQestionsRequiredCount('governance-question');
                    if (hasRequiredCount == 0) {
                        $('.no-mandatory-questions-msg').removeClass('d-none');
                    }
                    return;
                }
            } else {
                $('.governance-default').css({fill:"#3b64a2"});
            }
        }
        if ($('.environmental-tab').hasClass('disabledTab')) {
            $('.environmental-default').css({fill:"#949494"});
            if ( $('.environmental-tab').hasClass('environmental-tab-active')) {
                hasRequiredCount += getQestionsRequiredCount('environmental-question');
                if (hasRequiredCount == 0) {
                    $('.no-mandatory-questions-msg').removeClass('d-none');
                }
                return;
            }
        } else {
            if ( $('.environmental-tab').hasClass('environmental-tab-active')) {
                $('.environmental-default').css({fill:"#fff"});
            } else {
                $('.environmental-default').css({fill:"#006a4d"});
            }
        }
        if (hasRequiredCount == 0 && !$('.toggle-optional').hasClass('use-optional')) {
            $('.no-mandatory-questions-msg').removeClass('d-none');
        }
    }
    $('input:checkbox').change(function() {
        if ($(this).hasClass('toggle-form')) {
            if ($(this).is(':checked')) {
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('.slider').addClass('slider-on');
                    $('.file-upload').removeClass('d-none');
                    $('.manual-questions').addClass('d-none');
                })
            } else {
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('.slider').removeClass('slider-on');
                    $('.file-upload').addClass('d-none');
                    $('#records').addClass('d-none');
                    $('.manual-questions').removeClass('d-none');
                    $('.rev-counter-wrapper').hide();
                })
            }
        }
        if($(this).hasClass('toggle-optional')) {
            if ($(this).is(':checked')) {
                $('.required-only').addClass('d-none');
                $('.optional-plus').removeClass('d-none');
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('.slider').addClass('slider-on');
                    $('.slider').addClass('use-optional');
                    $('.is-optional').show();
                    $('.tab-item').each(function() {
                        if ($(this).hasClass('hasOptionalQuestions')) {
                            $(this).removeClass('disabledTab');
                        }
                    });
                    toggleTabColours();
                    $('.no-mandatory-questions-msg').addClass('d-none');
                    allQuestionCountlabelUpdate();
                })
            } else {
                $('.required-only').removeClass('d-none');
                $('.optional-plus').addClass('d-none');
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('.slider').removeClass('slider-on');
                    $('.slider').removeClass('use-optional');
                    $('.is-optional').hide();
                    $('.tab-item').each(function() {
                        if (!$(this).hasClass('hasRequiredQuestions')) {
                            $(this).addClass('disabledTab');
                        }
                    });
                    $('.no-mandatory-questions-msg').addClass('d-none');
                    $('.rev-counter-wrapper').hide();
                    toggleTabColours();
                    requiredQuestionCountlabelUpdate();
                })
            }
        }
        if ($(this).hasClass('question-toggle')) {
            var self = this;
            var target = $(this).attr('name');
            if ($(self).is(':checked')) {
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('[slider-name="'+ target +'"]').addClass('slider-on');

                })
            } else {
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('[slider-name="'+ target +'"]').removeClass('slider-on');
                })
            }
        }
    });
});
