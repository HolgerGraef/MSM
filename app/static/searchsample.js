var samples = new Bloodhound({
    datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
    queryTokenizer: Bloodhound.tokenizers.whitespace,
    remote: {
        url: '/search?autocomplete&term=%QUERY',
        wildcard: '%QUERY',
        transform: function(data) { return data.results; }
    }
});

function create_searchsample(searchfield) {
    searchfield.typeahead({
        minLength: 1,
        highlight: true
    }, {
        name: 'samples',
        display: function(result) { return result.name; },
        source: samples,
        templates: {
            suggestion: function(result) {
                if(result.parentname != '') {
                    parentinfo = '<span style="white-space:nowrap;"><i class="glyphicon glyphicon-level-up"></i>&nbsp;'+result.parentname+'</span>\n';
                } else {
                    parentinfo = '';
                }
                if(!result.mysample) {
                    ownerinfo = '<span style="white-space:nowrap;"><i class="glyphicon glyphicon-user"></i>&nbsp;'+result.ownername+'</span>\n';
                } else {
                    ownerinfo = '';
                }
                return '<div style="padding-left:2em;padding-bottom:0.5em;padding-top:0.5em;">\n'+
                       '<span style="white-space:nowrap;"><img src="/static/images/sample.png" style="margin-left:-1.5em;width:1.5em;height:1.5em;">&nbsp;'+result.name+'</span>\n'+
                       ownerinfo+
                       parentinfo+
                       '</div>';
            }
        }
    });
}

function create_selectsample(searchfield, hiddenfield, valid, placeholder) {
    // default values
    valid = valid || true;
    placeholder = placeholder || "None";

    searchfield.wrap("<div class=\"input-group\"></div>");
    searchfield.attr("placeholder", placeholder)

    var indicatorspan = $("<span class=\"input-group-addon\"></span>");
    var indicator = $("<i class=\"glyphicon glyphicon-"+(valid?"ok":"alert")+
                      "\" style=\"color:"+(valid?"green":"red")+";\"></i>");
    indicatorspan.append(indicator);
    searchfield.after(indicatorspan);

    searchfield.markvalid = function() {
        hiddenfield.attr('value', '');
        indicator.removeClass('glyphicon-alert');
        indicator.addClass('glyphicon-ok');
        indicator.css('color', 'green');
    };

    searchfield.markinvalid = function() {
        hiddenfield.attr('value', -1);
        indicator.removeClass('glyphicon-ok');
        indicator.addClass('glyphicon-alert');
        indicator.css('color', 'red');
    };

    searchfield.on('input', function() {
        if(searchfield.val() == '') {
            searchfield.markvalid();
        } else {
            searchfield.markinvalid();
        }
    });

    searchfield.bind('typeahead:select', function(ev, suggestion) {
        hiddenfield.attr('value', suggestion.id);
        indicator.removeClass('glyphicon-alert');
        indicator.addClass('glyphicon-ok');
        indicator.css('color', 'green');
    });

    create_searchsample(searchfield);
}