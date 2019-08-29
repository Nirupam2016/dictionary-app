$(document).ready(function(){
    (function() {
        //var inp_count = 1
        $('form').on('click', '.add_row', function() {
            //inp_count += 1;
            var start = $('.rep_field'),
                new_row = $('<tr><td><input type="text" size=30 name="symb_term"></td></tr>');
            $(start).append(new_row);
        });
    })();
});
