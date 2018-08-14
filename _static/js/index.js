let progress = '<div class="d-flex flex-justify-center" id="activity"><div data-role="activity" data-type="cycle" data-style="color"></div></div>';
let progresserror = '<div class="d-flex flex-justify-center"><p>Ой:( При выполнении запроса произошла ошибка! Администраторы исправят ее в ближайшее время</p></div>';
let progresserror_VNC = '<div class="d-flex flex-justify-center"><p>Ой:( Попытка подключения к удаленному компьютеру не удалась!</p></div>';
let active_VNC = 0;

$(function () {
    $('#group_selector').change(function () {
        let val = $(this).val();
        if (val !== '' && val !== '0')
            tableFuncs.addGroupFilter();
        else
            tableFuncs.removeGroupFilter();
    });
    if (!$("#filter").is(':checked'))
        tableFuncs.addArchiveFilter();
    setInterval(update_minion_table, 30000);
});

function update_minion_table ()
{
    let entities_table = $("#minion-table");
    let table;
    if (entities_table.length === 0) {
        return;
    }
    table = entities_table.data("table");
    table.loadData('/control_json/');
}

function onBeforeDraw_ () {
    $('#activity').removeClass('notshow');
    $('#minion-table-container').addClass('notshow');
}

function onDraw_ () {
    $('#activity').addClass('notshow');
    $('#minion-table-container').removeClass('notshow');
}

function onDrawRow_ (tr) {
    let state_val = tr.find('.cls_state')[0];
    let html = '';
    if (parseInt(state_val.innerHTML) === 0)
        html =  "<span class='fg-red mif-minus js-archive-record'></span>";
    else if (parseInt(state_val.innerHTML) === 1)
        html = "<span class='fg-green mif-checkmark'></span>";
    else if (parseInt(state_val.innerHTML) === 2)
        html = "<span class='fg-yellow mif-checkmark'></span>";
    else
        html = "<span class='fg-red mif-checkmark'></span>";

    $(state_val).html(html);
    state_val = tr.find('.cls_os')[0];
    html = state_val.innerHTML.indexOf('win') === 0 ? "<span class='mif-windows'></span>":
        state_val.innerHTML.indexOf('lin') === 0 ? "<span class='mif-linux'></span>": "<span class='mif-user'></span>";
    $(state_val).html(html);
    if (tr.find(".js-archive-record").length > 0) {
        tr.addClass("archive-record bg-lightGray")
    }
    tr.click(function (e) {
        actionsAboutMinion($(this).find('.id_col')[0].innerHTML
        );
    });
}

function actionsAboutMinion(elem) {
    active_VNC = elem;
    Metro.dialog.create({
        title: "Идет подключение...",
        overlay: true,
        content: function() {
            if (active_VNC && parseInt(active_VNC) > 0)
                elem = active_VNC + '/';
            else
                return progresserror;
            $.ajax({
                url: '/connectvnc/'+elem,
                success: function(url) {
                    var win = window.open(url, '_blank');
                    Metro.dialog.close('.dialog');
                    win.focus();
                },
                error: function() {
                    $('.dialog-content').html(progresserror_VNC);
                }
            });
            return progress
        },
        actions: [
            {
                caption: "Отмена",
                cls: "js-dialog-close",
            }
        ]
    });
}


function actionsAddGroup() {
    Metro.dialog.create({
        content: function() {
            group_id = $('#group_section').val();
            if (group_id && parseInt(group_id) > 0)
                group_id = group_id + '/';
            else
                group_id = '';
            $.ajax({
                url: '/add_group/'+group_id,
                success: function(data) {
                    $('.dialog-content').html(data);
                },
                error: function() {
                    $('.dialog-content').html(progresserror);
                }
            });
            return progress
        },
        overlay: true,
        clsAction: 'notshow',
        clsDialog: 'showTop',
        overlayClickClose: 'true',
        actions: [
                {
                    caption: "Закрыть",
                    cls: "js-dialog-close alert"
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
                onclick: function() {
                    alert("You choose NO");
                }
            }
        ]
    });
}

