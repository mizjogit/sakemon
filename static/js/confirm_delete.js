function confirmDelete(meme, post_to, params, on_success) {
    var cell = meme.parentNode;
    var original_class_name = meme.className
    meme.style.display = 'none'
    var cancel =  document.createElement('button');
    cancel.setAttribute('class',  "btn btn-sm");
    cancel.innerHTML = 'Cancel';
    cancel.onclick = function() { // cancelled. Remove buttons. redisplay glyph
        pe = this.parentElement 
        pe.lastElementChild.remove()
        pe.lastElementChild.remove()
        pe.lastElementChild.style.display = 'inherit'
    };
    cell.appendChild(cancel);
    var deleteButton = document.createElement('button');
    deleteButton.setAttribute('class', "btn btn-danger btn-sm");
    deleteButton.innerHTML = 'Confirm'
    deleteButton.onclick = function() { 
        // action_on_url('post', post_to, params);
        $.ajax({
            type: "POST",
            url: post_to,
            data: params,
            params: {
               lbutton: $(this),
            },
            success: function(data) {
                   //      TODO: fix up original item from this box, delete datatables row?
                   if (data.result == 'OK') {
                       console.log("OK: " + data.result + " " + data.message);
                       on_success(data);
                   } else {
                       console.log("Error: " + data.result + " " + data.message);
                   }
                }
            });
        return true;
    };
    cell.appendChild(deleteButton);
}
