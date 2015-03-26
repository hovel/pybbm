function pybb_delete_post(url, post_id, confirm_text) {
    conf = confirm(confirm_text);
    if (!conf) return false;
    obj = {url: url,
        type: 'POST',
        dataType: 'text',
        success: function (data, textStatus) {
            if (data.length > 0) {
                window.location = data;
            } else {
                $("#" + post_id).slideUp();
            }
        }
    };
    $.ajax(obj);
}

jQuery(function ($) {
    function getSelectedText() {
        if (document.selection) {
            return document.selection.createRange().text;
        } else {
            return window.getSelection().toString();
        }
    }

    var textarea = $('#id_body');

    if (textarea.length > 0) {
        $('.quote-link').on('click', function(e){
            e.preventDefault();
            var url = $(this).attr('href');
            $.get(
                url,
                function(data) {
                    if (textarea.val())
                        textarea.val(textarea.val() + '\n');
                    textarea.val(textarea.val() + data);
                }
            );
        });

        $('.quote-selected-link').on('click', function (e) {
            e.preventDefault();
            var selectedText = getSelectedText();
            if (selectedText != '') {
                if (textarea.val())
                    textarea.val(textarea.val() + '\n');

                var nickName = '';
                if ($(this).closest('.post-row').length == 1 &&
                    $(this).closest('.post-row').find('.post-username').length == 1) {
                    nickName = $(this).closest('.post').find('.post-username').text();
                }

                textarea.val(
                    textarea.val() +
                    (nickName ? ('[quote="' + $.trim(nickName) + '"]') : '[quote]') +
                    selectedText +
                    '[/quote]\n'
                );
            }
        });

        $('.post-row .post-username').on('click', function (e) {
            if (e.shiftKey) {
                var nick = $.trim($(this).text());
                if (textarea.val())
                    textarea.val(textarea.val() + '\n');
                textarea.val(textarea.val() + '[b]' + nick + '[/b], ');
                return e.preventDefault();
            }
        });
    }
});
