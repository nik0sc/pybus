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
function remove_polyline()
{
	if (drawn_polyline != null)
	{
		drawn_polyline.setMap(null);
		drawn_polyline = null;
	}
}

function draw_route(rt)
{
	// Draw route line (really point-to-point) on the map. Should write a better version
	// remove existing line
    remove_polyline();
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
				map: map,
				icon: {
					url: "/img/stop.90.png",
					scaledSize: new google.maps.Size(15, 15)
				}
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
    // init plugin
    $("#combo_service").combobox();
    
    // event handlers for inputs    	
	$("#combo_service").on("changed.fu.combobox", function(event, data){
		// update routes accordingly
        $.getJSON("/routes/" + data.text, function(data){
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
		// update stops accordingly
		var svc = $("#combo_service").combobox("selectedItem").text;
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
    	$("#alert_duplicate").slideUp();
    	
        var url = "/find_bus_extra/" + $("#combo_service").combobox("selectedItem").text  + "/" + $("#list_route").val() + "/" + $("#list_stop").val();
        console.log("Making request to "+ url);
        
        // make the request
        $.getJSON(url, function(data){
        	var next_mins =  Math.floor(data.rt[0].timings[0] / 60); 
            // attach it to the page
            if (data.next_bus.duplicate)
            {
            	// show warning of duplicate stop
            	$("#alert_duplicate").slideDown();
            }
            
            if (next_mins == 0)
            {
            	var text = "Your bus is " + data.next_bus.stop_distance + " stops away, and it's about to arrive in the next minute. It's now at " + data.next_bus.stop + " " + data.next_bus.desc + ".";
        	}
        	else
        	{
        		var text = "Your bus is " + data.next_bus.stop_distance + " stops away, or " + next_mins + " minutes away. It's now at " + data.next_bus.stop + " " + data.next_bus.desc + ".";
        	}
            $("#find_result").empty().append(text);
            draw_route(data.rt);
        })
        .fail(function(data){
            $("#find_result").empty().append("Can't find bus (" + data.responseJSON.error + ")");
        })
        .always(function(){
        	// once the XHR is finished, allow more presses
        	$("#btn_find").prop("disabled", false);
    	});
    });

    $("#btn_reset").click(function(){
        // throw away the app state
        // recenter the map 
        map.panTo(map_start);

        // remove all marks
        remove_polyline();
        remove_markers();

        // empty the route and stop selects
        update_options("#list_route", [], []);
        update_options("#list_stop", [], []);
        $("#combo_text_service").val("Pick one...");

        $("#find_result").empty().append("Reset!");
        $("#btn_find").prop("disabled", false);
        $("#alert_duplicate").hide();
            
    });
    
    $("#alert_duplicate_close").click(function(){
    	$("#alert_duplicate").slideUp();
    });

	// force update of routes etc
	//$("#list_service").change();
	
	// resize map_canvas div on browser resize
	$(window).resize(function(){
		$("#map_canvas").height($("body").height() - $("#inputs").outerHeight());
	})
	// and fire the event now
	.resize();
	
	/** Some notes from poking around this combobox control:
	 ** - The changed event fires when an option is selected, or when focus leaves the text input
	 ** - The event is not fired when the underlying text input is programmatically changed
	 */
	$("#combo_text_service").val("Pick one...");
	
	
	//.;

// end of $(function(){ ...
});
