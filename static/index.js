$(document).ready(function() {
    testchart = echarts.init(document.getElementById('summarypic'));
    var successNum = $('#success').text();
    var failNum = $('#fail').text();
    var errorNum = $('#error').text()
    var option = {
        title : {
            text : ""
        },
        tooltip: {
            show: true,
            trigger: 'item',
            formatter: "{b} : {c} ({d}%)"
        },
        legend:{
            zlevel:10
        },
        color: ["#5cb85c", "#d9534f", "#f0ad4e"],
        series : [
        {
            name: 'case概要',
            type: 'pie',
            radius: '75%',
            data:[
                {value:successNum, name:'成功'},
                {value:failNum, name:'失败'},
                {value:errorNum, name:'错误'}
            ]
        }
    ]
}
    testchart.setOption(option);

var dtable;
$(function() {
    //throw the exception on browser console instead of alerting
    $.fn.dataTable.ext.errMode = 'throw';
    dtable = $('#detailtable').DataTable({
        order: [[7, 'asc']],
        "lengthMenu": [
               [25, 50, 100, -1],
               [25, 50, 100, "All"]
           ],//每页显示条数设置
        "lengthChange": true,
        "bPaginate": true,
        "bFilter": false, 
        "searching": true,
        "ordering": true,
        "Info": true,
        "autoWidth": false,
        "serverSide": false,
        "pagingType": "full",
        "scrollX": "true",
        columns: [
            {"data": "name", "width": "10%"},
            {"data": "identity", "width": "10%"}, 
            {"data": "url", "width": "15%"}, 
            {"data": "type", "width": "5%"}, 
            {"data": "payload", "width": "15%"}, 
            {"data": "expect", "width": "10%"}, 
            {"data": "actual", "width": "20%"}, 
            {
                "data": "status",
                "width": "8%",
                "render": function(data, type, row, meta){
                    switch (row.status){
                        case "Success":
                            state_label = "label label-success";
                            break;
                        case "Fail":
                            state_label = "label label-danger";
                            break;
                        default:
                            state_label = "label label-warning";
                            break;
                    }
                    return '<span class="' + state_label + '">' + row.status + '</span>';
                }
            },
            {"data": "elapsed", "width": "7%"},    
        ],
        "language": {
            "search": "搜索",
            "lengthMenu": "_MENU_ 条记录每页",
            "zeroRecords": "没有找到记录",
            "sInfo": "当前显示 _START_ 到 _END_ 条，共 _TOTAL_ 条记录。",
            "infoEmpty": "无记录",
            "infoFiltered": "(从 _MAX_ 条记录过滤)",
            "paginate": {
                "previous": "上一页",
                "next": "下一页",
                "first": "首页",
                "last": "末页"
            }
        }  
    });
});

});





