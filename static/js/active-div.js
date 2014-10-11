// this does not destroy timers created in loaded elements that are replaced
function getMoreData(obj) {
        var href = obj.getAttribute('href');
        var timeout = obj.getAttribute('timeout');
        if (timeout == null) {
            timeout = 20000;
        }
        // clear the timers for the children that will get reloaded. If not we accumulate timers.
        $(obj).children().find('.active-div').each(function(ii, inner_obj) { 
            if ($(inner_obj)[0].timer) {
                clearTimeout($(inner_obj)[0].timer);
           }
        });
        console.log("loading " + href);
        $(obj).load(href, function() {
            hidden_status = obj.children[0]
            $(obj).children().find('.active-div').each(function(ii, inner_obj) { 
                getMoreData(inner_obj);
            });
            if (hidden_status && hidden_status.id == "status" && hidden_status.value == "Done") {
                $(obj).removeClass('active-div');  // make it no longer active
                console.log("Done remove adiv from class");
            } else {
                $(obj)[0].timer = setTimeout(getMoreData, timeout, obj);
            }
        });
 }
$(document).ready(function() {
    $.ajaxSetup({ cache: false });
    $(".active-div").each(function(i, obj) {
        getMoreData(obj);
    });
});
