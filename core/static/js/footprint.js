$(document).ready(function() {

    var token = $("input[name='csrfmiddlewaretoken']").prop("value");

    var htmlEncode = function (str) {
        if (str) {
            return str.replace(/<\/?[^>]+(>|$)/g, "");
        }
    };

    $(".form-group").each(function() {
        $(this).find("label").append( $(this).find("small"));
        $(this).find("small").addClass('mt-2').addClass('mb-2');
    });

    $(document).on('click', '.select2-selection__choice', function(e) {
        var target = $(e.target);
        if (! 'select2-selection__choice__remove' == target[0].className) {
            $('#id_material_risks').select2("close");
            var risk_id = $(this).attr('data-risk-id');
            if (risk_id) {
                $.ajax({
                    type: "POST",
                    url: $('.risk_description_url').text(),
                    data:  {
                        risk_id: risk_id,
                        industry: $('#id_industries').val()
                    },
                    beforeSend : function(jqXHR, settings) {
                        jqXHR.setRequestHeader("x-csrftoken", token);
                    },
                }).done(function( response ) {
                    $('#riskInfoModel').modal('show');
                    $('.modal-title').text(response.name);
                    $('.model-description').text(response.short_description);
                    $('.risk-source').text(response.source);
                });
            }
        }
    });

    var popOverSettings = {
        placement: 'right',
        container: 'td',
        trigger: 'focus',
        selector: '[rel="popover"]', //Sepcify the selector here
    };

    $('body').popover(popOverSettings);

    var destroyTable = function(tableClass) {
        $(tableClass).find("thead").empty();
        $(tableClass).find("tbody").empty();
    };
    var buildHeaders = function(tableClass, headData) {
        $(tableClass).find("thead").append("<tr>");
        $(tableClass).find("thead").find('tr').last().append('<th class="column-header" style="width: 20%">' + 'Risk Factor' + '</th>');
        $(tableClass).find("thead").find('tr').last().append('<th class="column-header"></th>');
        $.each(headData, function(index, value) {
            $(tableClass).find("thead").find('tr').last().append('<th class="column-header text-center" style="width: 2%">' + htmlEncode(value) + '</th>');
        });
    };
    var addRiskScores = function(headers, tableRow, risk, type) {
        var width = '150px;';
        if (headers.length > 3) {
            width = '100px;';
        }
        $.each(headers, function(index, header) {
            var added = false;
            for (var i = 2; i < risk.length; i++) {
                var TableType;
                if (type == 'industry') {
                    TableType = risk[i].industry;
                } else {
                    TableType = risk[i].country;
                }
                if (header == TableType) {
                    if (risk[i].score && risk[i].score == 0 || risk[i].score > 0) {
                        if (risk[i].risk_colour) {
                            if ("#ffe72f" == risk[i].risk_colour) {
                                tableRow.append(
                                    "<td class='row-text-item'>" +
                                        "<div class='risk-score' style='background-color: #ffe72f !important; width:" + width +"'>" +
                                        risk[i].score +
                                        "</div>" +
                                    "</td>"
                                );
                            } else {
                                tableRow.append(
                                    "<td class='row-text-item'>" +
                                        "<div class='risk-score risk-score-colour' style='background-color:" +  risk[i].risk_colour + "!important; width:" + width +"'>" +
                                        risk[i].score +
                                        "</div>" +
                                    "</td>"
                                );
                            }
                        } else {
                            tableRow.append(
                                "<td class='row-text-item'>" +
                                    "<div class='risk-score  risk-score-colour risk-dark-green' style=width:" + width +">" +
                                    risk[i].score +
                                    "</div>" +
                                "</td>"
                            );
                        }
                        added = true;
                    }
                    break;
                }
            }
            if (!added) {
                tableRow.append(
                    "<td class='row-text-item'>" +
                        "<div class='risk-score risk-score-colour risk-grey' style=width:" + width +">" +
                            'N/A' +
                        "</div>" +
                    "</td>"
                );
            }
        });
    };
    var addRiskAndPopover = function(risk, tableClass, tableRow) {
        tableRow.append(
            "<td class='row-text-item'>" +
                "<span class='risk-name'>" +
                    htmlEncode(risk[0]) +
                "</span>" +
            "</td>"
        );
        var popOver = "<td>" +
            "<a rel='popover' class='popButton' tabindex='0' data-title='' data-content=''>" +
                "<i class='fal question-mark fa-question-circle'></i>" +
            "</a>" +
        "</td>";
        tableRow.append(popOver);
        var popOverElement = $(tableClass).find("tbody").find('a').last();
        popOverElement.attr("data-title", htmlEncode(risk[0]));
        popOverElement.attr("data-content", htmlEncode(risk[1]));
    };
    var buildIndustryTable = function() {
        $.ajax({
            type: "POST",
            url: $('.industry_table_url').text(),
            data:  {
                industry: $('#id_industries').val(),
                risks: $('#id_material_risks').val(),
                assessment: $('.assessment-slug').attr('data-slug')
            },
            beforeSend : function(jqXHR, settings) {
                jqXHR.setRequestHeader("x-csrftoken", token);
            },
        }).done(function( response ) {
            var tableClass = '.industry-comparison';
            if($('.industry-comparison  > tbody tr').length > 0) {
                destroyTable(tableClass);
            }
            buildHeaders(tableClass, response.t_head_data);

            $.each(response.t_body_data, function(index, value) {
                $('.industry-comparison > tbody').append("<tr>");
                var tableRow = $(".industry-comparison  > tbody").find("tr").last();

                addRiskAndPopover(value, tableClass, tableRow);
                addRiskScores(response.t_head_data, tableRow, value, 'industry');
            });
            if ($('#id_countries').val().length > 0) {
                checkAndCalculateInherentRiskScore();
            }
        });
    };

    var buildGeoGraphicTable = function() {
        $.ajax({
            type: "POST",
            url: $('.geographic_table_url').text(),
            data:  {
                countries: $('#id_countries').val(),
                risks: $('#id_material_risks').val(),
                assessment: $('.assessment-slug').attr('data-slug')
            },
            beforeSend : function(jqXHR, settings) {
                jqXHR.setRequestHeader("x-csrftoken", token);
            },
        }).done(function( response ) {
            var tableClass = '.geo-comparison';
            if($('.geo-comparison > tbody tr').length > 0) {
                destroyTable(tableClass);
            }
            buildHeaders(tableClass, response.t_head_data);
            $.each(response.t_body_data, function(index, value) {
                $('.geo-comparison > tbody').append("<tr>");
                var tableRow = $(".geo-comparison > tbody").find("tr").last();

                addRiskAndPopover(value, tableClass, tableRow);
                addRiskScores(response.t_head_data, tableRow, value, 'country');
            });
            checkAndCalculateInherentRiskScore();
        });
    };

    var checkAndCallBuildCountryTable = function () {
        if (!$('.risk-toggle').hasClass('slider-on')) {
            return;
        }
        if ($('#id_countries').val().length > 0) {
            $('.geo-comparison-wrapper').show();
            buildGeoGraphicTable();
        } else {
            $('.geo-comparison-wrapper').hide();
            $('.inherent-comparison-wrapper').hide();
        }
    };
    var checkAndCallBuildIndustryTable = function () {
        if (!$('.risk-toggle').hasClass('slider-on')) {
            return;
        }
        if ($('#id_industries').val().length > 0) {
            buildIndustryTable();
            $('.industry-comparison-wrapper').show();
        } else {
            $('.industry-comparison-wrapper').hide();
        }
    };
    var checkAndCalculateInherentRiskScore = function () {
        $.ajax({
            type: "GET",
            url: $('.inherent_risk_url').text(),
            data:  {
                industry: $('#id_industries').val(),
                risks: $('#id_material_risks').val(),
                countries: $('#id_countries').val(),
                assessment: $('.assessment-slug').attr('data-slug')
            },
            beforeSend : function(jqXHR, settings) {
                jqXHR.setRequestHeader("x-csrftoken", token);
            },
            complete: function(response) {
                if ($('.risk-toggle').hasClass('slider-on') || $('.risk-toggle').hasClass('can-show-risk')) {
                    $('.inherent-comparison-wrapper').show();
                    var record;
                    if (response.responseJSON) {
                        record = response.responseJSON;
                    } else {
                        record = response;
                    }

                    $('.risk-score-text').html(record.score);
                    if ( record.score.includes("to")) {
                        $('.risk-score-text').css("font-size", 24 + "px").css('height', 65 + 'px');
                    }

                    if (record.colour) {
                        $('.risk-circle').css("background-color",record.colour);

                        if ('#ffe72f' === record.colour) {
                            $('.risk-score-text').css('color', '#808080');
                        } else {
                            $('.risk-score-text').css('color', '#fff');
                        }
                    }
                    if ($('.inherent-risk-text').length == 0) {
                        $('.inherent-comparison-wrapper').append("<div class='ml-2 inherent-risk-text'>" + ' The inherent risk rating is presented on a scale from Low to High; it is based on the average of the risk scores associated with the top five combined key impacts for that company.' + '</div>')
                    }
                }
            },
        });
    };
    $('input:checkbox').change(function() {
        if ($(this).hasClass('risk-checkbox')) {
            var self = this;
            var target = $(this).attr('name');
            if ($(self).is(':checked')) {
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('.slider').addClass('slider-on');
                });
                if ($('#id_countries').val().length > 0) {
                    $('.geo-comparison-wrapper').show();
                    buildGeoGraphicTable();
                    $('.slider').addClass('can-show-risk');
                    checkAndCalculateInherentRiskScore();
                } else {
                    $('.geo-comparison-wrapper').hide();
                }
                if ($('#id_industries').val().length > 0) {
                    buildIndustryTable();
                    $('.industry-comparison-wrapper').show();
                } else {
                    $('.industry-comparison-wrapper').hide();
                }
            } else {
                $('.slider').on('transitionend webkitTransitionEnd oTransitionEnd', function () {
                    $('.slider').removeClass('slider-on');
                });
                $('.industry-comparison-wrapper').hide();
                $('.geo-comparison-wrapper').hide();
                $('.inherent-comparison-wrapper').hide();
                $('.slider').removeClass('can-show-risk');
            }
        }
    });

    var updateIndustryDownloadList = function () {
        var industries = $('#id_industries').select2('data');
        $('#industry_ids').val('');
        $( industries ).each(function() {
            var oldIndustry = $('#industry_ids').val() + ',';
            $('#industry_ids').val(oldIndustry + this.id);
        });
    };

    var removeIndustryAddedRisks = function () {
        var existingRisks = $('#id_material_risks').select2('data');
        $( existingRisks ).each(function() {
            var newState = this.text.split(",");
            if (newState.length > 1) {
                $("#id_material_risks option[value=" + this.id + "]").remove();
            }
        });
    };

    updateIndustryDownloadList();

    var updateCountryDownloadList = function () {
        var countries = $('#id_countries').select2('data');
        $('#country_ids').val('');
        $( countries ).each(function() {
            var oldCountry = $('#country_ids').val() + ',';
            $('#country_ids').val(oldCountry + this.id);
        });
    };

    updateCountryDownloadList();

    $('#id_industries').change(function() {
        $.ajax({
            type: "POST",
            url: $('.industry_select_url').text(),
            data:  {
                industry: $(this).val(),
            },
            beforeSend : function(jqXHR, settings) {
                jqXHR.setRequestHeader("x-csrftoken", token);
            },
            complete: function(response) {
                updateIndustryDownloadList();
                removeIndustryAddedRisks();
                $.map(response.responseJSON.risks ,function(option) {
                    if ($('#id_material_risks').find("option[value='" + option.id + "']").length) {
                        $("#id_material_risks option[value=" + option.id + "]").remove();
                    }
                    var newOption = new Option(option.text, option.id, true, true);
                    $('#id_material_risks').append(newOption).trigger('change.select2');
                });
                checkAndCallBuildIndustryTable();
                checkAndCallBuildCountryTable();
                $('#industrySelectModal').modal('hide');
                $('.spinner').addClass('d-none');
                quickSave();
            },
        });
        var selected_industries = $(this).val()

        $('.industrySelect').each(function() {
            var inList = jQuery.inArray( $(this).attr("data-name"), selected_industries )
            if (inList !== -1) {
                if ($(this).prop("checked") == false) {
                    $(this).parent().parent().trigger('click', [ "updateDropdownFalse" ]);
                }
            } else {
                if ($(this).prop("checked") == true) {
                    $(this).parent().parent().trigger('click', [ "updateDropdownFalse", ]);
                }
            }
        });
    });

    var quickSave = function() {
        var form = $('#company_footprint');
        $.ajax({
            type: "POST",
            url: form.attr('action'),
            data: form.serialize(),
            success: function(data) {}
        });

    }
    $('#id_countries').change(function() {
        updateCountryDownloadList();
        checkAndCallBuildCountryTable();
        quickSave();
    });
    $('#id_material_risks').change(function() {
        if ($('#id_material_risks').val().length > 0) {
            checkAndCallBuildIndustryTable();
            checkAndCallBuildCountryTable();
        } else {
            $('.industry-comparison-wrapper').hide();
            $('.geo-comparison-wrapper').hide();
        }
        quickSave();
    });

    var browse = "<a class='float-right btn btn-secondary browse-btn'>" + 'Browse' + '</a>'
    $('#div_id_industries').append(browse)

    var browseAddedIndustries = [];
    var unchangedIndustries = [];

    $('.browse-btn').on('click touch', function (event) {
        $('#industrySelectModal').modal('show');
        for (var i = 0; i < $('#id_industries').val().length; i++) {
            browseAddedIndustries.push($('#id_industries').val()[i]);
            unchangedIndustries.push($('#id_industries').val()[i]);
        }
    });

    var updateIndustries = function (industry_id) {
        $.ajax({
            url: $('.toggle-select').attr('href'),
            type: "get",
            data: {
                'checked': 'true',
                'assessment_slug': $('.assessment-slug').attr('data-slug'),
                'industry_id': industry_id
            }
        });
    }

    $('.sublist-item').on('click tap', function(evt, param1) {
        var self = this;
        var checkBox = $(this).find('input:checkbox');
        var totalCount = parseInt($('.total-count').html());
        // Toggle checkbox
        checkBox.prop('checked', !checkBox.prop("checked"));
        if (checkBox.prop("checked") == true && totalCount >= 4) {
            checkBox.prop('checked', false);
            toastr.error('Cannot select more than 4 industries');
            return;
        }
        var countTag = checkBox.attr('data-count');
        var count = parseInt($(countTag).html());
        var numUp = count ;
        var selectedOption = $(this).find('input:checkbox').attr('data-name');
        if (checkBox.prop("checked")) {
            numUp += 1;
            $(countTag).text(numUp);
            $('.total-count').text(totalCount + 1);
            browseAddedIndustries.push(selectedOption);

        } else {
            numUp -= 1;
            $(countTag).text(numUp);
            $('.total-count').text(totalCount - 1);
            if (param1 == undefined) {
                var idx = $.inArray(selectedOption, browseAddedIndustries);
                if (idx !== -1) {
                    browseAddedIndustries.splice(idx, 1);
                }
            }
        }
        if (numUp > 0) {
            $(checkBox.attr('data-wrapper')).removeClass('d-none');
            $(checkBox).parent().parent().parent().parent().find('.industryTypeHeading').addClass('orange');
        } else {
            $(checkBox.attr('data-wrapper')).addClass('d-none');
            $(checkBox).parent().parent().parent().parent().find('.industryTypeHeading').removeClass('orange');
        }

    });

    $('.cancelBrowseAdd').on('click', function(evt, param1) {
        if (JSON.stringify(unchangedIndustries) !== JSON.stringify(browseAddedIndustries)) {
            $( unchangedIndustries ).each(function(idx, industry) {
                var chkBox =  $( "input[data-name*='" + industry   +"']" );
                var checked =  chkBox.prop('checked');
                if (checked == false) {
                    chkBox.prop('checked', true);
                    $(chkBox.attr('data-wrapper')).removeClass('d-none');
                    $(chkBox).parent().parent().parent().parent().find('.industryTypeHeading').addClass('orange');
                    var count = parseInt($(chkBox.attr('data-count')).html());
                    count += 1;
                    $(chkBox.attr('data-count')).text(count);
                    $('.total-count').text(parseInt($('.total-count').html()) + 1);
                }
            });
        }
        browseAddedIndustries = []
        unchangedIndustries = []
    });
    $('.confirmBrowseAdd').on('click tap', function(evt, param1) {
        $('.spinner').removeClass('d-none');
        if (JSON.stringify(unchangedIndustries) == JSON.stringify(browseAddedIndustries)) {
            browseAddedIndustries = [];
            unchangedIndustries = [];
            $('.spinner').addClass('d-none');
            return;
        }

        $( browseAddedIndustries ).each(function(idx, industry) {
            updateIndustries(industry)
        });

        $('#id_industries').val(browseAddedIndustries).trigger('change');

        browseAddedIndustries = []
    });

    if ($('.risk-checkbox').hasClass('start-on')) {
        $('.risk-checkbox').trigger('click');
    }
});