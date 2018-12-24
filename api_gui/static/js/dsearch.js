function dsearch_ajax_response(json_data,resdiv) {
    var respdata=jQuery.parseJSON(json_data)
    $(resdiv).html(respdata.ret);
    $('.conllu').each(function() {
	Annodoc.embedAnnotation($(this), Annodoc.parseConllU,
				Config.bratCollData);
    });
    $('#querylink').prop('href',respdata.query_link);
    $('#downloadlink').prop('href',respdata.download_link);
    $('#sourcelinks').html(respdata.source_links);
}

function dsearch_simulate_form(corpus,query,case_sensitive,hits_per_page) {
    $('#query').val(query);
    $('#treeset').val(corpus);
    if (case_sensitive=="true" || case_sensitive=="True" || case_sensitive=="checked") {
	$('#case').prop("checked",true);
    }
    else {
	$('#case').prop("checked",false);
    }
    $('#hits_per_page').val(hits_per_page);
    dsearch_run_ajax('#inpform','/query','#queryresult');
    //window.history.pushState("string", "", "/");
}

function dsearch_run_ajax(frm,path,resdiv) {
    $.ajax({
	url: $APP_ROOT+path,
	data: $(frm).serialize(),
	type: 'POST',
	beforeSend: function() { $(resdiv).html('');$(resdiv).hide(); $('#loading').show(); },
	complete: function() { $('#loading').hide(); $(resdiv).show(); },
	success: function(response){
	    dsearch_ajax_response(response,resdiv);
	},
	error: function(error){
	    $(resdiv).html('Backend server timeout.');
	    console.log("error, maybe timeout");
	    console.log(error);
	},
	fail: function(error){
	    $(resdiv).html('Backend server timeout.');
	    console.log("fail, maybe timeout");
	    console.log(error);
	},
	timeout:600000

    });
}

//hooks a form frm and result div resdiv to ajax path path
function ahook(frm,button,resdiv,path) {
    console.log("running ahook",frm, resdiv,path);
    $(frm).submit(function(e){
	dsearch_run_ajax(frm,path,resdiv);
	e.preventDefault();
    });
}

/*$(function() {
    $( ".autocomplete" ).autocomplete({
      source: $APP_ROOT+"/autocomplete",
      minLength: 2,
    });
});*/
  

$(function() {ahook('#inpform','#submitquery','#queryresult','/query');});



