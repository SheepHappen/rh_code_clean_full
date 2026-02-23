$(document).ready(function() {
    var htmlEncode = function (str) {
        if (str) {
            return str.replace(/<\/?[^>]+(>|$)/g, "");
        }
    };

    function formatSelectedIndustry(state) {
        var newState = state.text.split('_')
        if ($('.sasb_industry').length > 0) {
            if ($('.sasb_industry').length > 0) {
                var sasbIndustry = $('.sasb_industry').attr('data-sasb_industry');
            }
            if (sasbIndustry && newState[0] == sasbIndustry) {
                return $(
                    '<span>' +
                        htmlEncode('SASB: ' + newState[0]) +
                        '<span class="ml-3 inactive">' +
                            htmlEncode(newState[1]) +
                        '</span>' +
                    '</span>'
                );
            }
        }
        return $(
            '<span>' +
                htmlEncode(newState[0]) +
                '<span class="ml-3 inactive">' +
                    htmlEncode(newState[1]) +
                '</span>' +
            '</span>'
        );
    };

    function formatSelected(state, container) {
        var newState = state.text;
        if ($('.sasb_industry').length > 0) {
            var sasbIndustry = $('.sasb_industry').attr('data-sasb_industry');
        }
        if (sasbIndustry && sasbIndustry == newState[0]) {
            var title = '<i class="italics">SASB: </i>' + htmlEncode(newState[0]);
            state.title = title;
            $.ajax({
                url: $('.toggle-select').attr('href'),
                type: "get",
                data: {
                    'assessment_slug': $('.assessment-slug').attr('data-slug'),
                    'industry_name': htmlEncode(newState),
                    'checked': 'true',
                }
            })
            container.addClass('sasb-added');
            return $(
                '<span>' +
                    title +
                '</span>'
            );
        } else {
            var title = htmlEncode(newState);
            state.title = title;
            return $(
                '<span>' +
                    title +
                '</span>'
            );
        }
    };

    var industryOptionsUrl = $('.industry-options').attr('href');
    $('#id_industries').select2({
        placeholder:'Type to find',
        templateResult: formatSelectedIndustry,
        templateSelection: formatSelected,
        maximumSelectionLength: 4,
        ajax: {
            url: industryOptionsUrl,
            dataType: 'json',
            type: "GET",
            data: function (params) {
                return {
                    p: params.term,
                    page: params.page
                };
            },
            processResults: function (data, params) {
                return {
                    results: data.industries,
                };
            },
        },
    });

    $('#industrySelectModal').on('hidden.bs.modal', function () {
        $('.collapse').removeClass('show');
    });
});