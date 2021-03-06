$(document).ready(function () {
    $("#togbtn").on('change', function() {
    if ($(this).is(':checked')) {
        console.log("toggle_on");
        req = $.ajax({
            url : '/viewrooms',
            type : 'POST',
            data : { availableOnly : 1 },
            //success:function(response){ document.write(response);}
            success:function(response){ $("html").load("/viewrooms");}
        });
        $("head").append("<link rel='stylesheet' id='extracss' href='/static/css/Booking.css' type='text/css' />");
        console.log("css applied");
    }
    else {
        console.log("toggle_off");
        req = $.ajax({
            url : '/viewrooms',
            type : 'POST',
            data : { availableOnly : 0 },
            //success:function(response){ document.write(response);}
            success:function(response){ $("html").load("/viewrooms");}
        });
        $("head").append("<link rel='stylesheet' id='extracss' href='/static/css/Booking.css' type='text/css' />");
    }});
    $('input[type=radio][name=selector]').change(function() {
        if (this.value === 'asc') {
            console.log("ascending")
            req = $.ajax({
                url : '/viewrooms',
                type : 'POST',
                data : { srt : '0' },
                //success:function(response){ document.write(response);}
                success:function(response){ $("html").load("/viewrooms");}
            });
        }
        else if (this.value === 'desc') {
            console.log("descending")
            req = $.ajax({
                url : '/viewrooms',
                type : 'POST',
                data : { srt : '1' },
                //success:function(response){ document.write(response);}
                success:function(response){ $("html").load("/viewrooms");}
            });
        }
    });
    $('input[type=radio][name=food]').change(function() {
        console.log("Selecting Food")
        req = $.ajax({
            url : '/viewrooms',
            type : 'POST',
            data : { foodId : String(this.value) },
            //success:function(response){ document.write(response);}
            success:function(response){ $("html").load("/viewrooms");}
        });
    });
});