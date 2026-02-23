$(document).ready(function() {
    $("input[type=radio]").each(function() {
        if ($(this).is(':checked')) {
            $(this).parent().parent().parent().parent().addClass('document-active');
            $(this).parent().addClass('selected');
        } else {
            $(this).parent().parent().parent().parent().removeClass('document-active');
            $(this).parent().removeClass('selected');
        }
    });
    $( ".document-answer" ).click(function() {
        var element = $(this).find("input[type=radio]");
        element.prop("checked", true);
        // select active radio box
        $(this).parent().find("input[type=radio]").each(function() {
            if ($(this).is(':checked')) {
                $(this).parent().parent().parent().parent().addClass('document-active');
                $(this).parent().addClass('selected');
            } else {
                $(this).parent().parent().parent().parent().removeClass('document-active');
                $(this).parent().removeClass('selected');
            }
        });
        if ($('#documentChecklistForm').length > 0 && $('.toggle-counter').is(':checked')) {
            var form =  $('#documentChecklistForm');
            $.ajax({
                type: "POST",
                url: form.attr('action'),
                data: form.serialize(),
                success: function(data) {
                    $('.rev-text').text(data.revCounter + '%');
                    $('.rev-needle').css( {'transform': 'rotate('+ data.pin +'deg)'});
                    $('.due-dilligence-complete').text(data.percentageComplete);
                    $('.3-number-cirle').css( {'transform': 'rotate('+ data.pin + 2 +'deg)'});
                    $('.3-number').css( {'transform': 'rotate(-'+ data.pin +'deg)'});
                }
            });
        }

        // hide/show trigger questions.
        var inputValue = $(this).find("input[type=radio]").attr('value');
        var toggleId = element.attr('id');
        toggleId = toggleId.substring(0, toggleId.length - 1);

        $("ul[data-trigger-id="+ toggleId +"]").each(function( index ) {
            if (inputValue == 'Y') {
                $(this).removeClass('d-none');
                $(this).show();
            } else {
                $(this).addClass('d-none');
                $(this).hide();
            }
        });
    });

    $('.deleteManagementQUestion').click(function(e) {
        e.preventDefault();
        $.ajax({
            type: "GET",
            url: $(this).attr('href'),
            data: {
               'question_id': $(this).attr('hide'),
               'company_id': $(this).attr('company')
            }
        }).done(function( response ) {
            var newOption = new Option(response.question.text, response.question.id, false, false);
            $('#addQuestion').append(newOption).trigger('change.select2');
        });

        $("." + $(this).attr('hide') + "-hide").each(function( index ) {
            $(this).hide();
        });
    });
});
