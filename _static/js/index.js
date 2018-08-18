let progress = '<div class="d-flex flex-justify-center" id="activity"><div data-role="activity" data-type="cycle" data-style="color"></div></div>';
let progresserror = '<div class="d-flex flex-justify-center"><p>Ой:( При выполнении запроса произошла ошибка! Администраторы исправят ее в ближайшее время</p></div>';
let progresserror_VNC = '<div class="d-flex flex-justify-center"><p>Ой:( Попытка подключения к удаленному компьютеру не удалась!</p></div>';
let active_VNC = 0;

$(function () {
    $('#renamegr').css('display', 'none');
    $('#deletegr').css('display', 'none');

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
        overlay: true,
        clsAction: 'notshow',
        clsDialog: 'showTop',
        width: 900,
        overlayClickClose: 'true',
        content: function() {
            if (active_VNC && parseInt(active_VNC) > 0)
                elem = active_VNC + '/';
            else
                return progresserror;
            $.ajax({
                url: '/about/'+elem,
                success: function(data) {
                    $('.dialog-content').html(data);
                },
                error: function() {
                    $('.dialog-content').html(progresserror);
                }
            });
            return progress
        },
        actions: [
            {
                caption: "Закрыть",
                cls: "js-dialog-close alert",
            }
        ]
    });
}


function actionsVNCMinion(elem) {
    active_VNC = elem;
    Metro.dialog.create({
        title: "Идет подключение...",
        overlay: true,
        clsDialog: 'vnc_minion',
        content: function() {
            if (active_VNC && parseInt(active_VNC) > 0)
                elem = active_VNC + '/';
            else
                return progresserror;
            $.ajax({
                url: '/connectvnc/'+elem,
                success: function(url) {
                    var win = window.open(url, '_blank');
                    Metro.dialog.close('.vnc_minion');
                    win.focus();
                },
                error: function() {
                    $('.vnc_minion .dialog-content').html(progresserror_VNC);
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
            var data_path = $('.treeview li.current').attr('data-path');
            if ($('.treeview li.current').attr('data-sys') === '1')
                data_path = '';
            $.ajax({
                url: '/add_group/?parent='+data_path,
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


function actionsRenameGroup() {
    Metro.dialog.create({
        content: function() {
            group_id = $('.treeview li.current').attr('data-path');
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


function actionsDeleteGroup() {
    group_id = $('.treeview li.current').attr('data-path');
    if (group_id && parseInt(group_id) > 0)
        group_id = group_id + '/';
    else
        group_id = '';
    $.ajax({
        url: '/delete_group/'+group_id,
        success: function(data) {
            if (data === 'exists') {
                Metro.dialog.create({
                    title: 'Ошибка!',
                    content: '<div>В данной группе есть активные пользователи или у Вас недостаточно прав для ее редактирования ;(</div>',
                    overlay: true,
                    clsDialog: 'showTop',
                    overlayClickClose: 'true',
                    actions: [
                        {
                            caption: "Закрыть",
                            cls: "js-dialog-close alert"
                        }
                    ]
                });
            } else {
                $('#tree_li').html(data);
            }
        },
        error: function() {
            $('.dialog-content').html(progresserror);
        }
    });
}

function actionsGenAdminPIN() {
    Metro.dialog.create({
        content: function() {
            $.ajax({
                url: '/genadminpin/',
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

