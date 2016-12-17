/** pybus front-end JavaScript
 **	Nikos Chan, 2016  
 ** https://github.com/nik0sc/pybus
 */
"use strict";

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
		if (k == 0)
		{
			// draw marker at first coord
			drawn_markers.push(new google.maps.Marker({
				position: coords,
				map: map
			}));
		}
		else
		{
			drawn_markers.push(new google.maps.Marker({
				position: coords,
				map: map
				/*icon: {
					url: "/img/"
				}*/
			}));
		}
	});
	drawn_polyline = new google.maps.Polyline({
		path: line_coords,
		strokeColor: "#FF0000",
		strokeWeight: 3
	});
	drawn_polyline.setMap(map);
	

	
	// TODO: draw a bus icon between the last and second-last coords
	if (line_coords.length >= 2){
		// ugly af
		var midpoint = {
			lat: (line_coords[line_coords.length - 1].lat + line_coords[line_coords.length - 2].lat) / 2,
			lng: (line_coords[line_coords.length - 1].lng + line_coords[line_coords.length - 2].lng) / 2
		};
		drawn_markers.push(new google.maps.Marker({
			position: midpoint,
			map: map,
			icon: {
				url: "/img/bus.90.png",
				scaledSize: new google.maps.Size(48, 50),
				anchor: new google.maps.Point(24, 25)
			}
		}));
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
    	$("#find_result").empty().append("Finding...");
        var url = "/find_bus_extra/" + $("#list_service").val()  + "/" + $("#list_route").val() + "/" + $("#list_stop").val();
        // $("#find_url").empty().append(url);
        // make the request
        $.getJSON(url, function(data){
        	var next_mins = null; 
            // attach it to the page
            var text = "Your bus is " + data.next_bus.stop_distance + " stops away, or " + data.rt[0].timings[0] + " seconds away. It's now at " + data.next_bus.stop + " " + data.next_bus.desc + ".";
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

	// force update of routes etc
	//$("#list_service").change();
	
	// resize map_canvas div on browser resize
	$(window).resize(function(){
		$("#map_canvas").height($("body").height() - $("#inputs").outerHeight());
	})
	// and fire the event now
	.resize();

// end of $(function(){ ...
});
