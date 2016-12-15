/** pybus front-end JavaScript
 **	Nikos Chan, 2016  
 ** https://github.com/nik0sc/pybus
 */

var map;

function initMap()
{
	map = new google.maps.Map(document.getElementById("map_canvas"), {
		// Toa Payoh, Bishan, Serangoon, Ubi
		center: {lat: 1.3404926, lng: 103.8622066},
		zoom: 15
	});
}

function update_options(element, entries, values)
{
    //if (typeof values == "undefined"){
    //    values = entries;
    //}
    // remove child nodes (all option elements)
    $(element).empty();
    // then update
    // $.each(entries, function(i,v){ (is there a jQuery.zip()?)
    $(element).append($("<option disabled selected>Pick one...</option>"))
    for (var i = 0; i < entries.length; i++){
        $(element).append($("<option></option>")
            .attr("value", values[i])
            .text(entries[i]));
    } // );
    return;
}

var drawn_markers = [];
function remove_markers()
{
	$.each(drawn_markers, function(k,v){
		v.setMap(null);
	});
	drawn_markers = [];
}

var drawn_polyline = null;
function draw_route(rt)
{
	// Draw route line (really point-to-point) on the map. Should write a better version
	// remove existing line
	if (drawn_polyline != null)
	{
		drawn_polyline.setMap(null);
		drawn_polyline = null;
	}
	remove_markers();
	
	var bounds = new google.maps.LatLngBounds();
	var line_coords = [];
	$.each(rt, function(k,v){
		var coords = {lat: v.lat, lng: v.lng};
		bounds.extend(coords);
		line_coords.push(coords);
		// TODO: draw a simple stop icon here
	});
	drawn_polyline = new google.maps.Polyline({
		path: line_coords,
		strokeColor: "#FF0000",
		strokeWeight: 3
	});
	drawn_polyline.setMap(map);
	
	// draw marker at first coord
	drawn_markers.push(new google.maps.Marker({
		position: line_coords[0],
		map: map
	}));
	
	// TODO: draw a bus icon between the last and second-last coords
	if (line_coords.length >= 2){
		// ugly af
		var midpoint = {
			lat: (line_coords[line_coords.length - 1].lat + line_coords[line_coords.length - 2].lat) / 2,
			lng: (line_coords[line_coords.length - 1].lng + line_coords[line_coords.length - 2].lng) / 2
		};
		// then some means of finding the angle between these points, what, like real math???
	}
	// TODO: or else draw a bus icon approaching the only coords
	else
	{
	}
	
	map.fitBounds(bounds);
	return;
}


// execute when page ready
$(function(){
    // event handlers for <select>s	
	$("#list_service").change(function(){
		// update routes accordingly
		var svc = $(this).val();
        $.getJSON("/routes/" + svc, function(data){
            var entries = [];
            var values = [];
            // construct the strings to insert in #list_route
            $.each(data, function(i, v){
                entries.push(i + ": " + v.first_stop.Description + " to " + v.last_stop.Description);
                values.push(i);
            }); 
            update_options("#list_route", entries, values);
        });
        // force update of stops
        $("#list_route").change();
	});

	$("#list_route").change(function(){
		// update routes accordingly
		var svc = $("#list_service").val();
        var route = $(this).val();
        $.getJSON("/stops/" + svc + "/" + route, function(data){
            var entries = [];
            var values = [];
            // construct the strings to insert in #list_stop
            $.each(data, function(i, v){
                entries.push(v.BusStopCode + ": " + v.Description);
                values.push(v.BusStopCode);
            });
           update_options("#list_stop", entries, values);
        });
	});

    $("#btn_find").click(function(){
    	// prevent further button presses
    	$(this).prop("disabled", true);
        var url = "/find_bus_extra/" + $("#list_service").val()  + "/" + $("#list_route").val() + "/" + $("#list_stop").val();
        // $("#find_url").empty().append(url);
        // make the request
        $.getJSON(url, function(data){
        	var next_mins = 
            // attach it to the page
            var text = "Your bus is " + data.next_bus.stop_distance + " stops away, or " + data.rt[0].timings[0] + " seconds away. It's now at " + data.next_bus.stop+ " " + data.next_bus.desc + ".";
            $("#find_result").empty().append(text);
            draw_route(data.rt);
        })
        .fail(function(data){
            //$("#find_result").empty().append("find_bus failed, see server console (" + data.error + ")");
            $("#find_result").empty().append("find_bus failed, see server console");
        })
        .always(function(){
        	// once the XHR is finished, allow more presses
        	$("#btn_find").prop("disabled", false);
    	});
    });

	$("#about_link").click(function(){
		$("#about").show();
	});
	
	$("#about_close").click(function(){
		$("#about").hide();
	});

	// update services
	$.getJSON("/services", function(data){
		update_options("#list_service", data, data);
        // force update of routes etc
        $("#list_service").change();
	});

// end of $(function(){ ...
});
