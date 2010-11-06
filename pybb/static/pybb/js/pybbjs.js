function pybb_delete_post(url, post_id, confirm_text){
    conf = confirm(confirm_text);
    if (!conf) return false;
    obj = {url: url,
        type: 'POST',
        dataType: 'text',
        success: function (data, textStatus) {
            $("#" + post_id).slideUp();
        }
    };
    $.ajax(obj);
}
