function pybb_delete_post(url, post_id, confirm_text) {
    if (!confirm(confirm_text))
        return false;
    $.ajax({
        url: url,
        type: 'POST',
        dataType: 'text',
        success: function (data, textStatus) {
            if (data.length > 0) {
                window.location = data;
            } else {
                $("#" + post_id).slideUp();
            }
        }
    });
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
        $('.quote-link').on('click', function (e) {
            e.preventDefault();
            var url = $(this).attr('href');
            $.get(
                url,
                function (data) {
                    if (textarea.val())
                        textarea.val(textarea.val() + '\n');
                    textarea.val(textarea.val() + data);
                    window.location.hash = '#id_body';
                }
            );
        });

        $('.quote-selected-link').on('click', function (e) {
            if (!window.pybb.markup) {
                return true;
            }
            e.preventDefault();
            var selectedText = getSelectedText();
            if (selectedText != '') {
                if (textarea.val())
                    textarea.val(textarea.val() + '\n');
                var username = '';
                if ($(this).closest('.post-row').length == 1 &&
                    $(this).closest('.post-row').find('.post-username').length == 1) {
                    username = $.trim($(this).closest('.post').find('.post-username').text());
                }
                textarea.val(textarea.val() + window.pybb.markup.quote(selectedText, username));
                window.location.hash = '#id_body';
            }
        });

        $('.post-row .post-username').on('click', function (e) {
            if (window.pybb.markup && e.shiftKey) {
                e.preventDefault();
                var username = $.trim($(this).text());
                if (textarea.val())
                    textarea.val(textarea.val() + '\n');
                textarea.val(textarea.val() + window.pybb.markup.username(username));
                window.location.hash = '#id_body';
            }
        });
        
        var attachments_form = $('#id_body').closest('FORM').find('.attachments-form') ;
        
        if(attachments_form.length > 0){

            var first_file_id = attachments_form.find('.attachment-list .attachment-item INPUT[type=hidden]').attr('value');
            if(first_file_id){
                //if we are editing a post with an already attached files, attachment list must be displayed
                attachments_form.find('.attachment-list').show();
                attachments_form.find('.attachment-link').hide();
            }else{
                attachments_form.find('.attachment-list').hide();
                attachments_form.find('.attachment-link').show();
            }
            
            //Display "insert actions" only if we have a file for this attachment item.
            attachments_form.find('.attachment-ref').each(function(i){
                var file_id = $(this).closest('.attachment-item').find('INPUT[type=hidden]').attr('value');
                if(file_id){
                    $(this).show();
                }else{
                    $(this).hide();
                }
            });

            //some content is only usefull if JS works. By default these contents are not displayed.
            attachments_form.find('.attachment-ref-insert-link, .attachment-ref-insert-image').show().css('cursor', 'pointer');

            attachments_form.find('.attachment-link').on('click', function(e){
                /*Toggle attachment list and link to display it*/
                e.preventDefault();
                attachments_form.find('.attachment-link').toggle()
                $(this).closest('.attachments-form').find('.attachment-list').toggle();
            });

            attachments_form.find('.attachment-ref-insert-link').on('click', function(e){
                /*
                Insert link code with the file reference.
                Use window.pybb.insert_link to insert code, whatever markup language is used
                */
                e.preventDefault();
                var attachment_item = $(this).closest('.attachment-item'),
                    ref = attachment_item.find('.attachment-ref-value').text(),
                    file = attachment_item.find('INPUT[type=file]').get(0),
                    name = '';
                if(file && file.files && file.files[0]){
                    name = file.files[0].name ;
                }else if(file && file.value){
                    name = file.value.split('\\');
                    name = name[name.length - 1].split('/');
                    name = name[name.length - 1];
                }
                window.pybb.insert_link(ref, name);
            });

            attachments_form.find('.attachment-ref-insert-image').on('click', function(e){
                /*
                Insert image code with the file reference.
                Use window.pybb.insert_image to insert code, whatever markup language is used
                */
                e.preventDefault();
                var ref = $(this.parentNode).find('.attachment-ref-value').text();
                window.pybb.insert_image(ref);
            });

            function add_pybb_attachment_item() {
                /*
                Add another attachment formset when we just add a new file.
                */
                if(this.value){
                    $(this).unbind('change', add_pybb_attachment_item);
                    $(this).closest('.attachment-item').find('.attachment-ref').toggle();
                    var offset = parseInt($('#id_attachments-TOTAL_FORMS').attr('value')),
                        input_list, new_item;
                    if (offset < parseInt($('#id_attachments-MAX_NUM_FORMS').attr('value'))) {
                        input_list = attachments_form.find('.attachment-list');
                        new_item = input_list.find('.attachment-item').last().clone(true);
                        new_item.find('#id_attachments-'+ (offset-1) +'-id').attr('id', 'id_attachments-' + offset + '-id' ).attr('name','id_attachments-' + offset + '-id' );
                        new_item.find('#id_attachments-' + (offset-1) + '-file').replaceWith('<input id="id_attachments-' + offset + '-file" type="file" name="attachments-' + offset + '-file" />');
                        new_item.find('.attachment-ref-value').html('[file-' + (offset + 1) + ']');
                        input_list.append(new_item);
                        new_item.find('.attachment-ref').toggle();
                        $('#id_attachments-TOTAL_FORMS').attr('value', offset + 1);
                        current_input_file = $('#id_attachments-' + offset + '-file');
                        current_input_file.on('change', add_pybb_attachment_item);
                    };
                }
            }
            attachments_form.find('INPUT[type=file]').last().on('change', add_pybb_attachment_item);
        }
    }

    var $pybbConcernedTopics = $('#pybb_concerned_topics');
    if ($pybbConcernedTopics.length) {
        $('#pybb_subscription_type input[type="radio"]').change(function (e) {
            if (this.checked && (this.value == "2" || this.value == "unsubscribe")) {
                $pybbConcernedTopics.show();
            } else {
                $pybbConcernedTopics.hide();
            }
        });
        $pybbConcernedTopics.hide();
        $('input[name="type"][value="2"], input[name="type"][value="unsubscribe"]').each(function (i) {
            if (this.checked) {
                $pybbConcernedTopics.show();
            }
        });
    }
});
