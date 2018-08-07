let progress = '<div class="d-flex flex-justify-center" id="activity"><div data-role="activity" data-type="cycle" data-style="color"></div></div>';
let progresserror = '';

$(function () {
    if (!$("#filter").is(':checked'))
        tableFuncs.addArchiveFilter();
    $('#group_selector').change(function () {
        let val = $(this).val();
        if (val !== '' && val !== '0')
            tableFuncs.addGroupFilter();
        else
            tableFuncs.removeGroupFilter();
    });
    $('.cell-search input').val($('#searchS').val());
    //setInterval(update_minion_table, 3000);
});

function update_minion_table ()
{
    let filterstr = '?search='+$('.cell-search input').val();
    filterstr = filterstr+'&group='+$('#group_selector').val();
    if ($("#filter").is(':checked'))
        filterstr = filterstr+'&filtered=1';
    $('#minion-table-container').html(progress);
    $.ajax({
        url: '/control/'+encodeURI(filterstr),
        success: function(data) {
            $('#minion-table-container').html(data);
        },
        error: function () {
            $('#minion-table-container').html(progresserror);
        }
    });
}

function draw() {
    $('#minion-table tbody tr').click(function (e) {
        actionsAboutMinion($(this).find('.username').val());
    });
}

function actionsAboutMinion(elem){
    Metro.dialog.create({
        title: "Идет подключение...",
        content: progress,
        actions: [
            {
                caption: "Отмена",
                cls: "js-dialog-close",
            }
        ]
    });
}

function actionsDemo(){
    Metro.dialog.create({
        title: "Dialog actions",
        content: "<div>This dialog with custom actions</div>",
        actions: [
            {
                caption: "Yes, i'am",
                cls: "js-dialog-close alert",
                onclick: function(){
                    alert("You choose YES");
                }
            },
            {
                caption: "No, thanks",
                cls: "js-dialog-close",
                onclick: function(){
                    alert("You choose NO");
                }
            }
        ]
    });
}

function tablecreate(el){

}

