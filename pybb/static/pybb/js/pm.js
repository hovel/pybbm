function switchcb(cb, state)
{
    if(state) $(cb).attr('checked', 'checked').parent().parent().addClass('chosen');
    else $(cb).removeAttr('checked').parent().parent().removeClass('chosen');
    if($('.chosen').size()) $('#actionselect').removeAttr('disabled');
    else $('#actionselect').attr('disabled', 'disabled');
}
function multiaction(action)
{
    // TODO: i18n
    if(action=='delete' && !confirm(lang.deleting_messages_are_you_sure))
    {
        $('#actionselect').val('');
        return false;
    }
    $('#multiaction').get(0).submit();

}
$(document).ready(function(){
    $('#aselect_all').click(function(){
        $('.selectcb').each(function(){switchcb(this, true)});return false;
    });
    $('#aselect_none').click(function(){
        $('.selectcb').each(function(){switchcb(this, false)});return false;
    });
    $('#aselect_read').click(function(){
        $('.selectcb').each(function(){switchcb(this, true)});
        $('tr.new .selectcb').each(function(){switchcb(this, false)});return false;
    });
    $('#aselect_unread').click(function(){
        $('.selectcb').each(function(){switchcb(this, false)});
        $('tr.new .selectcb').each(function(){switchcb(this, true)});return false;
    });
    
    $('.selectcb').each(function(){switchcb(this, this.checked)}).click(function(){switchcb(this, this.checked)});
    $('#actionselect').val('').change(function(){multiaction(this.value)});
});